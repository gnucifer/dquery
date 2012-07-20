<?php
    if(isset($argv[1]) && file_exists($argv[1])) { 
        require $argv[1];
        $variable = isset($argv[2]) ? $argv[2] : 'db_url';
        print json_encode($$variable);
        exit(0);
    }
?>
