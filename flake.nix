{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    treefmt.url = "github:numtide/treefmt-nix";
    treefmt.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    treefmt,
  }: let
    forEachSystem = nixpkgs.lib.genAttrs [
      "aarch64-darwin"
      "aarch64-linux"
      "x86_64-linux"
    ];

    treefmtSettings = {
      projectRootFile = "flake.nix";

      programs = {
        nixfmt.enable = true;
        prettier.enable = true;
        ruff-format.enable = true;
      };
    };
  in {
    packages = forEachSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};

        python3 = pkgs.python3.override {
          packageOverrides = pyfinal: pyprev: {
            sphinx-favicon = pkgs.python3.pkgs.callPackage ./sphinx-favicon.nix {};
            sphinxext-rediraffe = pkgs.python3.pkgs.callPackage ./sphinxext-rediraffe.nix {};
          };
        };
      in {
        default = pkgs.stdenvNoCC.mkDerivation {
          name = "thinglab.org";

          src = self;

          nativeBuildInputs = [
            pkgs.svgbob
            python3.pkgs.dateutils
            python3.pkgs.feedgen
            python3.pkgs.furo
            python3.pkgs.myst-parser
            python3.pkgs.sphinx
            python3.pkgs.sphinx-copybutton
            python3.pkgs.sphinx-favicon
            python3.pkgs.sphinx-sitemap
            python3.pkgs.sphinxcontrib-spelling
            python3.pkgs.sphinxext-rediraffe
          ];

          env.NIX_LAST_MODIFIED_DATE = self.lastModifiedDate;

          buildPhase = ''
            sphinx-build -b dirhtml --fail-on-warning $src/content $out
            touch $out/.nojekyll
          '';

          dontInstall = true;
        };
      }
    );

    devShells = forEachSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        default = pkgs.mkShell {
          inputsFrom = [self.packages.${system}.default];

          env.DICPATH = "${pkgs.hunspellDicts.en_US-large}/share/hunspell";

          packages = [
            pkgs.python3.pkgs.sphinx-autobuild
          ];
        };
      }
    );

    formatter = forEachSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        treefmtEval = treefmt.lib.evalModule pkgs treefmtSettings;
      in
        treefmtEval.config.build.wrapper
    );

    checks = forEachSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        site = self.packages.${system}.default;
        treefmtEval = treefmt.lib.evalModule pkgs (
          treefmtSettings
          // {
            programs.ruff-check.enable = true;
          }
        );
      in {
        inherit site;

        formatting = treefmtEval.config.build.check self;

        vale = let
          valeStyles = pkgs.stdenvNoCC.mkDerivation {
            name = "vale-styles";

            dontUnpack = true;
            skipInstall = true;

            buildPhase = let
              google = pkgs.fetchFromGitHub {
                owner = "errata-ai";
                repo = "Google";
                rev = "7a56b623f9c555da38219529f9e3ce41cda5f376";
                hash = "sha256-ldwK9tMA04H/jTd3dQeRX/sZOwZcyPb+I56cDg0vZDg=";
              };
              microsoft = pkgs.fetchFromGitHub {
                owner = "errata-ai";
                repo = "Microsoft";
                rev = "c798f131106d77c136a3c1b5fa4916dee1de8edd";
                hash = "sha256-4j05bIGAVEy6untUqtrUxdLKlhyOcJsbcsow8OxRp1A=";
              };
              proselint = pkgs.fetchFromGitHub {
                owner = "errata-ai";
                repo = "proselint";
                rev = "1372bd30b7dcc526bd5b59bd244e167d975d30fd";
                hash = "sha256-swZU71rWgkm2lvaTpRL+1Wj7Y6ZMzN2ly6cXX+Zrqbs=";
              };
              readability = pkgs.fetchFromGitHub {
                owner = "errata-ai";
                repo = "readability";
                rev = "04fe2a19dc2b4d3df237345639a6c048d8b66e2c";
                hash = "sha256-5Y9v8QsZjC2w3/pGIcL5nBdhpogyJznO5IFa0s8VOOI=";
              };
            in ''
              mkdir $out
              cp -r ${google}/Google $out
              cp -r ${microsoft}/Microsoft $out
              cp -r ${proselint}/proselint $out
              cp -r ${readability}/Readability $out
            '';
          };
          valeConfig = pkgs.writeText "vale.ini" (
            nixpkgs.lib.generators.toINIWithGlobalSection {} {
              globalSection = {
                StylesPath = "${valeStyles}";
                MinAlertLevel = "suggestion";
                Packages = "Google, Microsoft, proselint, Readability";
              };
              sections."*" = {
                BasedOnStyles = "Vale, Google, Microsoft, proselint, Readability";
                # Spelling is covered by hunspell
                "Vale.Spelling" = "NO";
                # This is my blog, I get to use the first person
                "Google.FirstPerson" = "NO";
                "Microsoft.FirstPerson" = "NO";
                # TLAs are everywhere, using my best judgement
                "Google.Acronyms" = "NO";
                "Microsoft.Acronyms" = "NO";
                # same as Google.Headings
                "Microsoft.Headings" = "NO";
                # same as Google.We
                "Microsoft.We" = "NO";
                # same as Microsoft.Contractions
                "Google.Contractions" = "NO";
                # Lower the level of these
                "Readability.LIX" = "suggestion";
                "Readability.FleschReadingEase" = "suggestion";
                "Google.Exclamation" = "suggestion";
              };
            }
          );
        in
          pkgs.runCommand "vale" {} ''
            ${pkgs.vale}/bin/vale --config=${valeConfig} $(find ${self} -iname '*.md')
            touch $out
          '';

        exif = pkgs.runCommand "exiftool" {} ''
          for image in ${self}/content/images/*.{jpg,png}; do
            data=$(${pkgs.exiftool}/bin/exiftool -GPS:all -n "$image")
            if [ -n "$data" ]
            then
              echo "Location data exists in $image"
              exit 1
            else
              echo "No location data in $image"
            fi
          done
          touch $out
        '';

        spelling = self.packages.${system}.default.overrideAttrs (oA: {
          name = "spelling";
          env =
            oA.env
            // {
              DICPATH = "${pkgs.hunspellDicts.en_US-large}/share/hunspell";
            };
          buildPhase = ''
            sphinx-build -b spelling --fail-on-warning content $out
          '';
        });
      }
    );
  };
}
