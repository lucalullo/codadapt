"""Block updates; all row-dependent training state stays local to this module."""

from time import perf_counter

import numpy as np

from ._core import GAIN_RTOL, addresses, aggregate, gain, sigmoid


def data_loss(y, score, weight, binary):
    loss = np.logaddexp(0.0, score) - y * score if binary else 0.5 * (y - score) ** 2
    return float(np.dot(weight, loss))


def objective(model, y, score, weight, binary):
    penalty = sum(float(np.dot(v, v)) for v in model.main_tables_ + model.tables_)
    return data_loss(y, score, weight, binary) + 0.5 * model.l2 * penalty


def _surrogate(y, score, old, weight, binary):
    if binary:
        return weight / 4.0, old + 4.0 * (y - sigmoid(score))
    return weight, y - (score - old)


def _selected_groups(feature_gains, n_tables):
    """Select a bounded set of high-signal pairs without scanning all combinations."""
    p = len(feature_gains)
    if not n_tables or not p:
        return []
    if p == 1:
        return [np.array([0], dtype=np.intp)]
    order = np.argsort(-np.asarray(feature_gains), kind="stable")
    groups, seen = [], set()
    for offset in range(1, p):
        for start in range(p):
            pair = tuple(sorted((int(order[start]), int(order[(start + offset) % p]))))
            if pair in seen:
                continue
            seen.add(pair)
            groups.append(np.asarray(pair, dtype=np.intp))
            if len(groups) == n_tables:
                return groups
    return groups


def predict_coded_memory_buckets(levels, encoders, z_levels, intercept, table_size):
    """Add level memories for already encoded inputs."""
    result = np.full(len(z_levels[0]), intercept, dtype=np.float64)
    for level, encoder, z in zip(levels, encoders, z_levels):
        main_features = level.get("main_features", range(len(level["main_tables"])))
        for feature, values in zip(main_features, level["main_tables"]):
            result += values[z[:, feature]]
        for features, codes, values in zip(level["groups"], level["codes"], level["tables"]):
            index = addresses(z, features, codes, table_size)
            supported = np.ones(len(z), dtype=bool)
            for feature in features:
                supported &= encoder.support_[feature][z[:, feature]]
            result += np.where(supported, values[index], 0.0)
    return result


def train_coded_memory(model, z_levels, y, weight, z_valid_levels, y_valid, rng):
    """Allocate a fixed lookup budget to residual feature and interaction memories."""
    binary = model._task == "classification"
    n, p = z_levels[0].shape
    mean = float(np.average(y, weights=weight))
    if binary:
        positive_mass = float(weight[y == 1].sum())
        negative_mass = float(weight[y == 0].sum())
        model.intercept_ = float(np.log(positive_mass) - np.log(negative_mass))
    else:
        model.intercept_ = mean
    score = np.full(n, model.intercept_, dtype=np.float64)
    model.levels_, model.level_history_, model.allocation_history_ = [], [], []
    model.training_history_ = []
    model.timings_.update(
        score_updates=0.0,
        code_search=0.0,
        validation=0.0,
        restore=0.0,
        residual=0.0,
        candidate_selection=0.0,
        candidate_scoring=0.0,
        candidate_application=0.0,
    )
    interactions_enabled = model.n_tables > 0
    stopping_enabled = model.early_stopping and z_valid_levels is not None
    collision_aware = True
    shared_screening = True
    active_feature_mask = np.ones(p, dtype=bool)
    previous_feature_gains = np.full(p, np.inf, dtype=np.float64)
    screening_seconds = 0.0
    prefilter_discarded = 0
    fully_screened = 0
    remaining_budget = int(model.lookup_budget)
    cumulative_memory = 0
    cumulative_penalty = 0.0
    best_validation = None
    if z_valid_levels is not None:
        initial = np.full(len(y_valid), model.intercept_, dtype=np.float64)
        if binary:
            best_validation = float(np.mean(np.logaddexp(0.0, initial) - y_valid * initial))
        else:
            best_validation = float(np.mean((y_valid - initial) ** 2))

    for level_number, (z, encoder) in enumerate(zip(z_levels, model.encoders_), start=1):
        if remaining_budget <= 0:
            break
        level_started = perf_counter()
        score_before = score.copy()
        penalty_before = cumulative_penalty
        objective_before = data_loss(y, score, weight, binary)
        objective_before += 0.5 * model.l2 * cumulative_penalty
        levels_remaining = len(z_levels) - level_number + 1
        level_budget = max(1, remaining_budget // levels_remaining)

        screening_started = perf_counter()
        candidate_features = np.flatnonzero(active_feature_mask)
        h, residual_target = _surrogate(y, score, np.zeros(n), weight, binary)
        screened_features = candidate_features
        if shared_screening and len(candidate_features):
            sample_step = max(1, n // 512)
            sample = np.arange(0, n, sample_step, dtype=np.intp)[:512]
            sample_response = h[sample] * residual_target[sample]
            cheap_scores = []
            for feature in candidate_features:
                size = encoder.n_buckets_[feature]
                mass = np.bincount(z[sample, feature], minlength=size)
                response = np.bincount(z[sample, feature], weights=sample_response, minlength=size)
                cheap_scores.append(float(np.dot(response, response / (mass + model.l2))))
            pool_size = min(
                len(candidate_features),
                max(2 * max(1, level_budget), (len(candidate_features) + 1) // 2),
            )
            cheap_order = np.argsort(-np.asarray(cheap_scores), kind="stable")
            screened_features = candidate_features[cheap_order[:pool_size]]
            discarded = candidate_features[cheap_order[pool_size:]]
            active_feature_mask[discarded] = False
            prefilter_discarded += len(discarded)
        feature_gains = np.zeros(p, dtype=np.float64)
        for feature in screened_features:
            a, b = aggregate(z[:, feature], h, residual_target, encoder.n_buckets_[feature])
            feature_gains[feature] = gain(a, b, model.l2)
        fully_screened += len(screened_features)
        order = screened_features[np.argsort(-feature_gains[screened_features], kind="stable")]
        maximum_feature_gain = float(feature_gains[order[0]]) if len(order) else 0.0
        feature_slots = (
            level_budget if not interactions_enabled else max(1, (2 * level_budget) // 3)
        )
        selected_features = [
            int(feature)
            for feature in order
            if feature_gains[feature] >= 0.02 * maximum_feature_gain
        ][: min(feature_slots, p)]
        if not model.main_effects or maximum_feature_gain <= GAIN_RTOL:
            selected_features = []
        if shared_screening:
            selected_set = set(selected_features)
            for feature in screened_features:
                weak_relative = feature_gains[feature] < 0.03 * maximum_feature_gain
                weak_progress = (
                    np.isfinite(previous_feature_gains[feature])
                    and feature_gains[feature] < 0.10 * previous_feature_gains[feature]
                )
                if feature not in selected_set or weak_relative or weak_progress:
                    active_feature_mask[feature] = False
                else:
                    previous_feature_gains[feature] = feature_gains[feature]
        screening_seconds += perf_counter() - screening_started

        main_tables = []
        for feature in selected_features:
            h, residual_target = _surrogate(y, score, np.zeros(n, dtype=np.float64), weight, binary)
            a, b = aggregate(z[:, feature], h, residual_target, encoder.n_buckets_[feature])
            values = b / (a + model.l2)
            score += values[z[:, feature]]
            cumulative_penalty += float(np.dot(values, values))
            main_tables.append(values)

        interaction_slots = min(model.n_tables, max(0, level_budget - len(selected_features)))
        interaction_candidates = []
        if interactions_enabled and interaction_slots:
            candidate_count = min(max(2 * interaction_slots, 1), max(2 * model.n_tables, 1))
            for features in _selected_groups(feature_gains, candidate_count):
                group_codes = [
                    rng.randint(model.table_size, size=encoder.n_buckets_[feature]).astype(
                        np.uint16
                    )
                    for feature in features
                ]
                index = addresses(z, features, group_codes, model.table_size)
                h, residual_target = _surrogate(
                    y, score, np.zeros(n, dtype=np.float64), weight, binary
                )
                a, b = aggregate(index, h, residual_target, model.table_size)
                candidate_gain = gain(a, b, model.l2)
                combinations = int(np.unique(z[:, features], axis=0).shape[0])
                occupied = int(np.unique(index).size)
                collisions = max(0, combinations - occupied)
                collision_rate = collisions / combinations if combinations else 0.0
                utility = (
                    candidate_gain / (1.0 + 3.0 * collision_rate)
                    if collision_aware
                    else candidate_gain
                )
                interaction_candidates.append(
                    (
                        utility,
                        candidate_gain,
                        collision_rate,
                        combinations,
                        collisions,
                        features,
                        group_codes,
                    )
                )
            interaction_candidates.sort(key=lambda item: item[0], reverse=True)

        codes, groups, tables = [], [], []
        collision_counts, combination_counts = [], []
        top_interaction_gain = max(
            (candidate[1] for candidate in interaction_candidates), default=0.0
        )
        for candidate in interaction_candidates:
            if len(tables) >= interaction_slots:
                break
            _, candidate_gain, collision_rate, combinations, collisions, features, group_codes = (
                candidate
            )
            if candidate_gain < 0.05 * top_interaction_gain:
                continue
            if (
                collision_aware
                and collision_rate > 0.55
                and candidate_gain < 0.5 * top_interaction_gain
            ):
                continue
            index = addresses(z, features, group_codes, model.table_size)
            h, residual_target = _surrogate(y, score, np.zeros(n, dtype=np.float64), weight, binary)
            a, b = aggregate(index, h, residual_target, model.table_size)
            values = b / (a + model.l2)
            score += values[index]
            cumulative_penalty += float(np.dot(values, values))
            groups.append(features)
            codes.append(group_codes)
            tables.append(values)
            collision_counts.append(collisions)
            combination_counts.append(combinations)

        lookup_count = len(selected_features) + len(tables)
        if lookup_count == 0:
            break
        level_memory = sum(values.nbytes for values in main_tables + tables)
        level_memory += sum(code.nbytes for group in codes for code in group)
        total_combinations = int(sum(combination_counts))
        total_collisions = int(sum(collision_counts))
        collision_rate = total_collisions / total_combinations if total_combinations else 0.0
        level = {
            "n_bins": int(model.resolution_bins_[level_number - 1]),
            "main_features": np.asarray(selected_features, dtype=np.intp),
            "main_tables": main_tables,
            "groups": groups,
            "codes": codes,
            "tables": tables,
        }
        candidate_levels = model.levels_ + [level]
        validation_loss = None
        validation_gain = np.nan
        if z_valid_levels is not None:
            validation_started = perf_counter()
            validation_prediction = predict_coded_memory_buckets(
                candidate_levels,
                model.encoders_[:level_number],
                z_valid_levels[:level_number],
                model.intercept_,
                model.table_size,
            )
            if binary:
                validation_loss = float(
                    np.mean(
                        np.logaddexp(0.0, validation_prediction) - y_valid * validation_prediction
                    )
                )
            else:
                validation_loss = float(np.mean((y_valid - validation_prediction) ** 2))
            validation_gain = float(best_validation - validation_loss)
            model.timings_["validation"] += perf_counter() - validation_started

        objective_value = data_loss(y, score, weight, binary)
        objective_value += 0.5 * model.l2 * cumulative_penalty
        gain_per_lookup = (objective_before - objective_value) / lookup_count
        accepted = not stopping_enabled or validation_gain > model.tol * max(
            1.0, abs(best_validation)
        )
        residual = y - sigmoid(score) if binary else y - score
        history = {
            "level": level_number,
            "n_bins": level["n_bins"],
            "accepted": bool(accepted),
            "active_features": selected_features,
            "active_interactions": len(tables),
            "lookup_count": lookup_count,
            "train_loss": float(data_loss(y, score, weight, binary) / weight.sum()),
            "objective": float(objective_value),
            "validation_loss": validation_loss,
            "validation_gain": float(validation_gain),
            "gain_per_lookup": float(gain_per_lookup),
            "residual_mean_abs": float(np.average(np.abs(residual), weights=weight)),
            "fit_seconds": float(perf_counter() - level_started),
            "added_memory_bytes": int(level_memory),
            "collision_count": total_collisions,
            "combination_count": total_combinations,
            "collision_rate": float(collision_rate),
        }
        model.allocation_history_.append(history.copy())
        if not accepted:
            score = score_before
            cumulative_penalty = penalty_before
            break

        model.levels_.append(level)
        cumulative_memory += int(level_memory)
        remaining_budget -= lookup_count
        history["cumulative_memory_bytes"] = int(cumulative_memory)
        model.level_history_.append(history)
        model.training_history_.append(
            {
                "iteration": len(model.levels_),
                "train_loss": history["train_loss"],
                "objective": history["objective"],
                "validation_loss": validation_loss,
                "coordinates_examined": 0,
                "accepted_moves": 0,
                "candidates_evaluated": len(interaction_candidates),
            }
        )
        if validation_loss is not None:
            best_validation = validation_loss

    model.main_tables_ = [values for level in model.levels_ for values in level["main_tables"]]
    model.groups_ = [group for level in model.levels_ for group in level["groups"]]
    model.codes_ = [codes for level in model.levels_ for codes in level["codes"]]
    model.tables_ = [values for level in model.levels_ for values in level["tables"]]
    model.level_memory_bytes_ = int(cumulative_memory)
    model.effective_levels_ = len(model.levels_)
    model.active_features_per_level_ = [len(level["main_features"]) for level in model.levels_]
    model.active_interactions_ = sum(len(level["tables"]) for level in model.levels_)
    model.lookup_count_per_sample_ = sum(
        len(level["main_tables"]) + len(level["tables"]) for level in model.levels_
    )
    model.n_iter_ = len(model.levels_)
    model.screening_seconds_ = float(screening_seconds)
    model.prefilter_discarded_ = int(prefilter_discarded)
    model.fully_screened_candidates_ = int(fully_screened)
    model.feature_level_stopping_ = int(np.count_nonzero(~active_feature_mask))
    model.best_iteration_ = model.n_iter_
    model.accepted_moves_ = 0
