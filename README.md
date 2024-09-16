## pm5 (Process Manager) - README

### Overview

`pm5` is a Python package inspired by [pm2](https://pm2.keymetrics.io/), designed to easily manage multiple services and their configurations. It is particularly useful for advanced scenarios where precise control over CPU usage, service monitoring, and automatic restarts are required. This package was created to overcome limitations in managing multiple Celery queues and workers, allowing for more granular control of allocated CPU.

`pm5` is a simple tool for developers and system administrators who need advanced control over multiple services and their configurations. Its ability to manage resources, automate restarts, and handle graceful shutdowns makes it an essential tool for complex service management scenarios.

### Use Cases

- **Managing Multiple Celery Queues**: Gain fine-grained control over the number of workers per queue, overcoming limitations of Celery's worker management.
- **Service Stack Management**: Manage and configure multiple services as a single stack, simplifying the deployment and monitoring process.
- **Advanced Resource Management**: Allocate CPU resources more effectively across multiple services, ensuring optimal performance and resource utilization.

### Features

- **Service Management**: Start, stop, and monitor multiple services with ease.
- **Advanced CPU Management**: Control the number of instances per service based on CPU availability.
- **Automatic Restarts**: Automatically restart services on failure with configurable restart limits.
- **Environment Management**: Pass specific environment variables to each service.
- **Graceful Shutdown**: Handle graceful shutdowns and cleanups of services.
- **Configuration Flexibility**: Easily configure services through a JSON ecosystem file.

### Installation

```bash
pip install pm5
```

### Configuration

Create an ecosystem configuration file (e.g., `ecosystem.config.json`) to define the services you want to manage.

#### Example `ecosystem.config.json`

```json
{
  "services": [
    {
      "name": "Test Application 1",
      "interpreter": "python3.9",
      "interpreter_args": [],
      "script": "test.py",
      "args": [],
      "instances": 1,
      "wait_ready": true,
      "autorestart": true,
      "max_restarts": 3,
      "env": {
        "ENV_VAR": "value"
      },
      "disabled": false
    }
  ]
}
```

### Configuration Fields

| Field             | Type      | Example            | Description                                                                        |
|-------------------|-----------|--------------------|------------------------------------------------------------------------------------|
| `disabled`        | boolean   | false              | Enable or disable the service                                                      |
| `name`            | string    | Test Application 1 | The name of the service used for debugging                                         |
| `interpreter`     | string    | python3.9          | The path to the interpreter                                                        |
| `interpreter_args`| string[]  | []                 | The args passed to the interpreter                                                 |
| `script`          | string    | test.py            | The script to call                                                                 |
| `args`            | string[]  | []                 | The args passed to the script                                                      |
| `instances`       | number    | 1                  | The number of instances of the script to run                                       |
| `wait_ready`      | boolean   | true               | Wait for the service to load before continuing to the next service                 |
| `autorestart`     | boolean   | true               | Automatically restart the service                                                  |
| `max_restarts`    | number    | 3                  | The number of times to autorestart the service if failure before exiting           |
| `env`             | object    | {}                 | An object of environment key values that should be passed to the script            |

### Usage

#### Help

```shell
❯ pm5 --help
usage: pm5 [-h] {start,stop} ...

Like pm2 but without node.js.

positional arguments:
  {start,stop}
    start       Start the process manager daemon
    stop        Stop the process manager daemon

optional arguments:
  -h, --help    show this help message and exit
```

#### Start the stack as a daemon

```shell
pm5 start
```

#### Stop the daemonized stack

```shell
pm5 stop
```

#### Start the app without daemonizing
```shell
pm5 start --debug
```
