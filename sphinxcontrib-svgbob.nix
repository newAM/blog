{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  sphinx,
  setuptools,
  setuptools-rust,
  rustPlatform,
  rustc,
  cargo,
  pytestCheckHook,
}:

buildPythonPackage rec {
  pname = "sphinxcontrib-svgbob";
  version = "0.3.0";

  src = fetchFromGitHub {
    owner = "newAM";
    repo = "sphinxcontrib-svgbob";
    rev = "a43014978c4eb2f2a403b71af0f4e488acca41c2";
    hash = "sha256-m+LmmG/N505mzLHocFcGzIzKUH4FZQIhBI+P5d7UNlI=";
  };

  cargoDeps = rustPlatform.fetchCargoTarball {
    inherit src;
    sourceRoot = "${src.name}/sphinxcontrib/svgbob/_svgbob";
    name = "${pname}-${version}";
    hash = "sha256-S7o4pshSInmAxYCxX0wKaN+gEwinhtDkpEpHU+ZxaKQ=";
  };

  cargoRoot = "sphinxcontrib/svgbob/_svgbob";

  build-system = [
    setuptools
    setuptools-rust
  ];

  dependencies = [
    sphinx
  ];

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustc
    cargo
  ];

  nativeCheckInputs = [
    pytestCheckHook
  ];

  preCheck = ''
    python setup.py build_ext --inplace
  '';

  pythonImportsCheck = [ "sphinxcontrib.svgbob" ];

  pythonNamespaces = [ "sphinxcontrib" ];

  meta = {
    description = "Sphinx extension to convert ASCII diagrams to SVGs with Svgbob";
    homepage = "https://github.com/sphinx-contrib/svgbob";
    changelog = "https://github.com/sphinx-contrib/svgbob/blob/v${version}/CHANGELOG.md";
    license = lib.licenses.mit;
    maintainers = [ lib.maintainers.newam ];
  };
}
