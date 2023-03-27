import jinja2

from slxpy.common.mapping import simulink_mapping

def add_filters(env: jinja2.Environment):
    env.filters["prefix"] = lambda s, prefix: prefix + s
    def field_desc(s: str):
        for m in simulink_mapping:
            if s.endswith(f"_{m[1]}"):
                return m[2]
        return "Unknown"
    env.filters["field_desc"] = field_desc
    env.filters["select_struct"] = lambda l: [s for s in l if not s.is_enum]
    env.filters["select_enum"] = lambda l: [s for s in l if s.is_enum]
