{ pkgs, ... }:
{
  packages = with pkgs; [
    libmysqlclient
  ];

  services.mysql.enable = true;
  services.mysql.ensureUsers = [
    {
      name = "test";
      password = "1234";
      ensurePermissions = {
        "*.*" = "ALL PRIVILEGES";
      };
    }
  ];
  services.mysql.initialDatabases = [
    {
      name = "test";
    }
  ];
}
