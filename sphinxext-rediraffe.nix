{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  sphinx,
  setuptools,
}:

buildPythonPackage rec {
  pname = "sphinxext-rediraffe";
  version = "0.2.7";

  src = fetchFromGitHub {
    owner = "wpilibsuite";
    repo = "sphinxext-rediraffe";
    tag = "v${version}";
    hash = "sha256-g+GD1ApD26g6PwPOH/ir7aaEgH+n1QQYSr9QizYrmug=";
  };

  postPatch = ''
    substituteInPlace setup.py \
        --replace-fail 'version = "main"' 'version = "${version}"'
  '';

  build-system = [
    setuptools
  ];

  dependencies = [
    sphinx
  ];

  pythonImportsCheck = [ "sphinxext.rediraffe" ];

  pythonNamespaces = [ "sphinxext" ];

  meta = {
    description = "Sphinx extension to redirect files";
    homepage = "https://github.com/wpilibsuite/sphinxext-rediraffe";
    license = lib.licenses.mit;
    maintainers = [ lib.maintainers.newam ];
  };
}
