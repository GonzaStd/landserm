schema = {
    'backup': {
        "enabled": {
            "type": "bool",
            "nullable": False
        },
        "repositories": {
            "type": "list[path]",
            "nullable": True
        }
    },

    'space': {
        "enabled": {
            "type": "bool",
            "nullable": False
        },
        "partitions": {
            "type": "list[partuuid]",
            "nullable": True
        }
    },

    'mount': {
        "enabled": {
            "type": "bool",
            "nullable": False
        },
        "partitions": {
            "type": "list[partuuid]",
            "nullable": True
        }
    }
}
