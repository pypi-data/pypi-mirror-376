# fmi-bd2cmake

CMakeLists.txt generator that reads buildDescription.xml in FMI source code and generates build files for CMake.

## Installation

Install from PyPI (when published):
```bash
pip install fmi-bd2cmake
```

Or install from source:
```bash
git clone https://github.com/jgillis/fmi-bd2cmake.git
cd fmi-bd2cmake
pip install -e .
```

## Usage

Navigate to your FMU directory structure and run:

```bash
# Basic usage (looks for sources/buildDescription.xml in current directory)
fmi-bd2cmake

# Specify custom input/output paths
fmi-bd2cmake --input path/to/buildDescription.xml --output MyProject.txt

# Get help
fmi-bd2cmake --help
```

## Expected Directory Structure

The tool expects an FMU source directory structure like:

```
your_fmu_directory/
├── sources/
│   ├── buildDescription.xml
│   ├── model.c
│   └── utils.c
└── CMakeLists.txt (generated)
```

After running `fmi-bd2cmake`, you can build with:

```bash
cmake -B build -DFMI_HEADERS_DIR=/path/to/fmi/headers .
cmake --build build
cmake --install build
```

This will create a shared library in `binaries/{arch}/` directory as per FMI convention.

## buildDescription.xml Format

The tool supports FMI 2.0 buildDescription.xml format with the following elements:

```xml
<fmiBuildDescription fmiVersion="2.0">
  <BuildConfiguration description="Build config" modelIdentifier="my_model">
    <SourceFileSet language="C99">
      <SourceFile name="model.c"/>
      <SourceFile name="utils.c"/>
      <IncludeDirectory name="../include"/>
      <PreprocessorDefinition name="DEBUG"/>
      <PreprocessorDefinition name="VERSION" value="1.0"/>
    </SourceFileSet>
    <IncludeDirectory name="../../common"/>
    <Library name="m"/>
    <PreprocessorDefinition name="PLATFORM_LINUX"/>
  </BuildConfiguration>
</fmiBuildDescription>
```

## Features

- **Standard library only**: No external dependencies beyond Python standard library
- **Cross-platform**: Automatically detects target architecture (x86_64-linux, x86_64-windows, etc.)
- **Full FMI support**: Handles source files, include directories, preprocessor definitions, and libraries
- **FMI headers support**: Optional specification of external FMI header directory (typically containing fmi2Functions.h)
- **Multiple source file sets**: Supports different language/compiler settings per source set
- **CMake best practices**: Generates modern CMake with proper target properties
- **Error handling**: Clear error messages for missing files or invalid XML

## FMI Headers Configuration

FMI header files (such as `fmi2Functions.h`) are typically not included in the FMU source distribution. The generated CMakeLists.txt automatically attempts to locate these headers and provides several ways to specify their location:

### CMake Variable
```bash
cmake -DFMI_HEADERS_DIR=/path/to/fmi/headers .
```

### Environment Variable
```bash
export FMI_HEADERS_DIR=/path/to/fmi/headers
cmake .
```

### Automatic Discovery
The generated CMakeLists.txt will automatically search for FMI headers in common locations:
- `/usr/include/fmi2` (Ubuntu/Debian libfmi-dev package)
- `/usr/local/include/fmi2` (custom installation)
- `/opt/local/include/fmi2` (MacPorts)
- `../fmi-headers` (relative to project)
- `fmi-headers` (in project directory)

The CMake variable takes precedence over the environment variable, which takes precedence over automatic discovery.

## Examples

See the `test_example/` and `test_advanced/` directories for working examples.
