{ pkgs ? (import <nixpkgs> { }).pkgs }:
with pkgs;

# To run (CUDA):
# python -m venv env
# source env/bin/activate
# pip install -r requirements.txt
# python run.py --execution-providers cuda

mkShell {
  buildInputs = [ (python3.withPackages (ps: with ps; [ virtualenv numpy ])) ];
  APPEND_LIBRARY_PATH =
    "${lib.makeLibraryPath [ libGL glib ]}:${stdenv.cc.cc.lib}/lib/";
  shellHook = ''
    LD_LIBRARY_PATH="$APPEND_LIBRARY_PATH:$LD_LIBRARY_PATH"
  '';
}
