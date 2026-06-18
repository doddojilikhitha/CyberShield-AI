{ pkgs }: {
    deps = [
        pkgs.python312Packages.pip
        pkgs.python312Full
        pkgs.nodejs_20
        pkgs.libffi
        pkgs.sqlite
        pkgs.openssl
    ];
}
