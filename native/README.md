# Historical native inference sources

The C++ files are preserved byte-for-byte from the supplied public 2.1.0 repository. They are not compiled or shipped as native extension binaries by the 2.2.0 Python build. Native-platform performance and prior qualification receipts cannot be inherited by a new binary. The current backend builds a pure-Python wheel only. Historical workflow filenames now validate that Python distribution and do not certify a native binary. See [compatibility](../docs/COMPATIBILITY.md).
