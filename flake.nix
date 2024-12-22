{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # nix flakes do not support submodules natively
    # see: https://github.com/NixOS/nix/pull/7862
    abridge.url = "github:jieiku/abridge";
    abridge.flake = false;
  };

  outputs =
    {
      self,
      nixpkgs,
      abridge,
    }:
    let
      forEachSystem = nixpkgs.lib.genAttrs [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];
    in
    {
      packages = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.stdenvNoCC.mkDerivation {
            name = "thinglab.org";

            src = self;

            nativeBuildInputs = [ pkgs.zola ];

            # need to remove static directory to workaround:
            # https://github.com/getzola/zola/issues/2677
            buildPhase = ''
              mkdir themes
              cp -r ${abridge} themes/abridge
              chmod +w -R themes/abridge
              rm themes/abridge/static/*.{png,ico,svg}
              zola build --output-dir $out
            '';

            dontInstall = true;
          };
        }
      );

      checks = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          site = self.packages.${system}.default;
        in
        {
          inherit site;

          markdown_format = pkgs.runCommand "prettier" { } ''
            ${pkgs.nodePackages.prettier}/bin/prettier --check ${self}/content ${self}/README.md
            touch $out
          '';

          nix_format = pkgs.runCommand "nixfmt" { } ''
            ${pkgs.nixfmt-rfc-style}/bin/nixfmt --check ${self}/flake.nix
            touch $out
          '';

          toml_format = pkgs.runCommand "taplo" { } ''
            cd ${self}
            ${pkgs.taplo}/bin/taplo fmt --check
            touch $out
          '';

          vale =
            let
              valeStyles = pkgs.stdenvNoCC.mkDerivation {
                name = "vale-styles";

                dontUnpack = true;
                skipInstall = true;

                buildPhase =
                  let
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
                  in
                  ''
                    mkdir $out
                    cp -r ${google}/Google $out
                    cp -r ${microsoft}/Microsoft $out
                    cp -r ${proselint}/proselint $out
                    cp -r ${readability}/Readability $out
                  '';
              };
              valeConfig = pkgs.writeText "vale.ini" (
                nixpkgs.lib.generators.toINIWithGlobalSection { } {
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
                    # Lower the level of these
                    "Readability.LIX" = "suggestion";
                    "Readability.FleschReadingEase" = "suggestion";
                  };
                }
              );
            in
            pkgs.runCommand "vale" { } ''
              ${pkgs.vale}/bin/vale --config=${valeConfig} ${self}/**/*.md
              touch $out
            '';

          exif = pkgs.runCommand "exiftool" { } ''
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

          spellcheck =
            pkgs.runCommand "spellcheck"
              {
                buildInputs = with pkgs; [
                  (hunspellWithDicts [ hunspellDicts.en-us-large ])
                ];
              }
              ''
                LANG="en_US.UTF-8" hunspell -p ${./words.txt} -l -H ${site}/**/*.html | tee mistakes.txt
                [ $(wc -l < mistakes.txt) -gt 0 ] && exit 1
                touch $out
              '';
        }
      );
    };
}
