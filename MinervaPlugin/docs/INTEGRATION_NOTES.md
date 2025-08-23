## PCC Integration Notes for Dynamic Commands

This plugin now treats all non-`stream` commands as dynamic and simply enqueues
raw dicts. PCC should own semantics and dispatch via string-based handlers.

- Stream remains controlled by the plugin via `_handle_stream_control` heartbeats.
- Start payload should not carry steps; PCC resolves steps from assay/settings.

Integration example (PCC):

1) Use the provided example dispatcher
```
from PCC_command_dispatcher_example import PCCDispatcher

dispatcher = PCCDispatcher()

# New seeded command handlers
dispatcher.register_handler('initialize_rig', lambda cmd: start_run(cmd.get('payload')))
dispatcher.register_handler('go_to_next', lambda cmd: advance_mode())
dispatcher.register_handler('go_to_step', lambda cmd: jump_to_step((cmd.get('payload') or {}).get('step')))
dispatcher.register_handler('send_filename', lambda cmd: load_file((cmd.get('payload') or {}).get('filename')))
dispatcher.register_handler('stop_experiment', lambda cmd: stop_experiment())

# Legacy command support for backward compatibility
dispatcher.register_handler('start', lambda cmd: start_run(cmd.get('payload')))  # maps to initialize_rig
dispatcher.register_handler('load_pups', lambda cmd: load_file((cmd.get('payload') or {}).get('filename')))  # maps to send_filename
```

2) Poll and dispatch within PCC loop (where you can access `plugin`):
```
commands = plugin.pop_commands()
for cmd in commands:
    if not dispatcher.dispatch(cmd):
        logger.debug(f"Unhandled command: {cmd}")
```

3) Notes
- If legacy clients send Start with `steps` in payload, ignore them.
- `stop_stream` should be treated as advisory; plugin uses heartbeat TTL for stopping.

