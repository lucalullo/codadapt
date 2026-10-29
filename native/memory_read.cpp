// CodAdapt contract 1: ordered coded-memory reads, no training or state mutation.
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cstdint>
#include <cstring>
#include <vector>
#include <utility>

namespace py = pybind11;
using Index = py::ssize_t;

// memcpy supports unaligned and strided borrowed NumPy buffers without casts.
template<class T> T load(const char* p) {
    T value;
    std::memcpy(&value, p, sizeof(T));
    return value;
}

struct Vector {
    py::array owner;
    const char* data;
    Index size, stride;
    Vector(py::handle object, const py::dtype& type) {
        if (!py::isinstance<py::array>(object)) throw py::type_error("Expected ndarray, no implicit cast");
        owner = py::reinterpret_borrow<py::array>(object);
        if (owner.ndim() != 1 || !owner.dtype().equal(type)) throw py::type_error("Invalid vector dtype/shape");
        data = static_cast<const char*>(owner.data());
        size = owner.shape(0); stride = owner.strides(0);
    }
    template<class T> T at(Index i) const {
        if (i < 0 || i >= size) throw py::index_error("Coded-memory bucket outside buffer");
        return load<T>(data + i*stride);
    }
};

struct Code {
    py::array owner;
    const char* data;
    Index size, stride;
    char kind;
    int width;
    explicit Code(py::handle object) {
        if (!py::isinstance<py::array>(object)) throw py::type_error("Expected integral ndarray code");
        owner = py::reinterpret_borrow<py::array>(object);
        auto dt = owner.dtype(); kind = dt.kind(); width = static_cast<int>(dt.itemsize());
        if (owner.ndim() != 1 || (kind != 'i' && kind != 'u') ||
            (width != 1 && width != 2 && width != 4 && width != 8) ||
            !py::cast<bool>(dt.attr("isnative"))) throw py::type_error("Invalid code dtype/shape/byte order");
        data = static_cast<const char*>(owner.data()); size = owner.shape(0); stride = owner.strides(0);
    }
    std::uint64_t at(Index i) const {
        if (i < 0 || i >= size) throw py::index_error("Code bucket outside buffer");
        const auto* p = data + i*stride;
        if (kind == 'i') {
            switch (width) {
                case 1: return static_cast<std::uint64_t>(load<std::int8_t>(p));
                case 2: return static_cast<std::uint64_t>(load<std::int16_t>(p));
                case 4: return static_cast<std::uint64_t>(load<std::int32_t>(p));
                default: return static_cast<std::uint64_t>(load<std::int64_t>(p));
            }
        }
        switch (width) {
            case 1: return load<std::uint8_t>(p);
            case 2: return load<std::uint16_t>(p);
            case 4: return load<std::uint32_t>(p);
            default: return load<std::uint64_t>(p);
        }
    }
};

std::vector<Index> features(py::handle input, Index columns) {
    std::vector<Index> result;
    for (auto item: py::reinterpret_borrow<py::iterable>(input)) {
        PyObject* indexed = PyNumber_Index(item.ptr());
        if (!indexed) throw py::error_already_set();
        auto value = py::reinterpret_steal<py::object>(indexed).cast<Index>();
        if (value < 0 || value >= columns) throw py::index_error("Feature outside encoded columns");
        result.push_back(value);
    }
    return result;
}

struct Main {
    Index feature;
    Vector values;
};
struct Group {
    std::vector<Index> features;
    std::vector<Code> codes;
    std::vector<Vector> support;
    Vector values;
};
struct Level {
    py::array z;
    const char* data;
    Index rows, columns, row_stride, col_stride;
    std::vector<Main> mains;
    std::vector<Group> groups;
    Level(py::handle z_object, py::dict level, py::sequence supports, Index table_size) {
        if (!py::isinstance<py::array>(z_object)) throw py::type_error("Expected encoded ndarray");
        z = py::reinterpret_borrow<py::array>(z_object);
        if (z.ndim() != 2 || !z.dtype().equal(py::dtype::of<std::uint16_t>()))
            throw py::type_error("Encoded input must be native uint16 matrix");
        rows = z.shape(0); columns = z.shape(1); row_stride = z.strides(0); col_stride = z.strides(1);
        data = static_cast<const char*>(z.data());
        auto main_values = level["main_tables"].cast<py::sequence>();
        std::vector<Index> main_features;
        if (level.contains("main_features")) main_features = features(level["main_features"], columns);
        else for (Index f = 0; f < py::len(main_values); ++f) {
            if (f >= columns) throw py::index_error("Too many main tables");
            main_features.push_back(f);
        }
        if (main_features.size() != static_cast<size_t>(py::len(main_values)))
            throw py::value_error("Main feature/table count mismatch");
        for (size_t i = 0; i < main_features.size(); ++i)
            mains.push_back({main_features[i], Vector(main_values[i], py::dtype::of<double>())});
        auto group_features = level["groups"].cast<py::sequence>();
        auto group_codes = level["codes"].cast<py::sequence>();
        auto group_values = level["tables"].cast<py::sequence>();
        if (py::len(group_features) != py::len(group_codes) || py::len(group_features) != py::len(group_values))
            throw py::value_error("Group/code/table count mismatch");
        for (Index g = 0; g < py::len(group_features); ++g) {
            Group item{features(group_features[g], columns), {}, {},
                       Vector(group_values[g], py::dtype::of<double>())};
            auto codes = group_codes[g].cast<py::sequence>();
            if (item.features.size() != static_cast<size_t>(py::len(codes)) || item.values.size != table_size)
                throw py::value_error("Group code count or table size mismatch");
            for (size_t i = 0; i < item.features.size(); ++i) {
                auto feature = item.features[i];
                if (feature >= py::len(supports)) throw py::index_error("Missing feature support");
                item.codes.emplace_back(codes[i]);
                item.support.emplace_back(supports[feature], py::dtype::of<bool>());
            }
            groups.push_back(std::move(item));
        }
    }
    std::uint16_t bucket(Index row, Index feature) const {
        return load<std::uint16_t>(data + row*row_stride + feature*col_stride);
    }
};

Index address(std::uint64_t bits, Index table_size) {
    if ((table_size & (table_size-1)) == 0) return static_cast<Index>(bits & (table_size-1));
    // NumPy int64 addition wraps. Derive mathematical signed remainder from the
    // two's-complement bits without signed overflow or implementation-defined cast.
    if (bits <= UINT64_C(0x7fffffffffffffff)) return static_cast<Index>(bits % table_size);
    auto magnitude_mod = ((~bits) + 1) % static_cast<std::uint64_t>(table_size);
    return magnitude_mod ? table_size-static_cast<Index>(magnitude_mod) : 0;
}

py::array_t<double> predict_head(py::sequence levels, py::sequence supports,
                                 py::sequence encoded, double intercept, Index table_size) {
    if (table_size <= 0 || table_size > 65536) throw py::value_error("table_size outside contract 1..65536");
    // Early stopping can retain a prefix (including zero levels) of the encoder
    // ladder. Unused encoded levels are legitimate and must not be read.
    if (py::len(encoded) == 0 || py::len(levels) > py::len(encoded) || py::len(levels) > py::len(supports))
        throw py::value_error("Missing level support/input or empty encoded ladder");
    if (!py::isinstance<py::array>(encoded[0])) throw py::type_error("Expected encoded ndarray");
    auto first = py::reinterpret_borrow<py::array>(encoded[0]);
    if (first.ndim() != 2 || !first.dtype().equal(py::dtype::of<std::uint16_t>()))
        throw py::type_error("Encoded input must be native uint16 matrix");
    const auto rows = first.shape(0);
    std::vector<Level> parsed;
    for (Index i = 0; i < py::len(levels); ++i) {
        parsed.emplace_back(encoded[i], levels[i].cast<py::dict>(), supports[i].cast<py::sequence>(), table_size);
        if (parsed.back().rows != rows) throw py::value_error("Row count mismatch");
    }
    py::array_t<double> result(rows);
    auto* out = result.mutable_data();
    // Keep GIL: inputs are borrowed, and no mutable native cache survives this call.
    for (Index row = 0; row < rows; ++row) {
        double score = intercept;
        for (const auto& level: parsed) {
            for (const auto& main: level.mains) score += main.values.at<double>(level.bucket(row, main.feature));
            for (const auto& group: level.groups) {
                std::uint64_t sum = 0;
                bool supported = true;
                for (size_t f = 0; f < group.features.size(); ++f) {
                    auto bucket = level.bucket(row, group.features[f]);
                    sum += group.codes[f].at(bucket);
                    // Do not short-circuit validation of the remaining support buffers.
                    bool present = group.support[f].at<std::uint8_t>(bucket) != 0;
                    supported = supported && present;
                }
                double value = group.values.at<double>(address(sum, table_size));
                score += supported ? value : 0.0;
            }
        }
        out[row] = score;
    }
    return result;
}

PYBIND11_MODULE(_native_kernel, module) {
    module.attr("contract_version") = 1;
    module.def("predict_head", &predict_head, "Ordered memory read; no implicit array conversions");
}
