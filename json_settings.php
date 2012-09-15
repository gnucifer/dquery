<?php
  //exit status
  //1: variable not found
  //TODO: more exit statuses
    if(isset($argv[1]) && file_exists($argv[1])) { 
        require $argv[1];
        $variable = isset($argv[2]) ? $argv[2] : 'db_url';
        if(isset($$variable)) {
          print json_encode($$variable);
          exit(0);
        }
        exit(1);
    }
?>
