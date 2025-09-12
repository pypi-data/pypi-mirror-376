{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.default = let
        pythonPkgs = pkgs.python312Packages;
      in pkgs.mkShell {
        packages = with pkgs; [
          python312
          pythonPkgs.pip
          pythonPkgs.virtualenv
          pythonPkgs.build
          pythonPkgs.ipython
          pythonPkgs.ruff
          oh-my-zsh
          jq
          neofetch
          git
          htop
          curl
          ripgrep
          tmux
          unzip
          zsh
        ];

        shellHook = ''
          export SHELL=$(which zsh)
          exec zsh
        '';
      };
    });
}
