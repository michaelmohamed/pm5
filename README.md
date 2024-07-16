# pm5 (process manager)

1. Install pm5 via: `pip install pm5`
2. Create an ecosystem file (e.g. `ecosystem.config.json`)
3. Run `pm5` to start all configured services

| Field | Type | Example | Description |
|---|---|---|---|
| disabled | boolean | false | Enable or disable the service |
| name | string | Test Application 1 | The name of the service used for debugging |
| interpreter | string | python3.9 | The path to the interpreter |
| interpreter_args | string[] | [] | The args passed to the interpreter |
| script | string | test.py | The script to call |
| args | string[] | [] | The args passed to the script |
| instances | number | 1 | The number of instance of the script to run |
| wait_ready | boolean | true | Wait for the service to load before continuing to the next service |
| autorestart | boolean | true | Automatically restart the service |
| max_restarts | number | 3 | The number of times to autorestart the service if failure before exiting |
| env | object | {} | An object of environment key values that should be passed to the script |






