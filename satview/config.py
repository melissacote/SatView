import yaml


def load_config(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ValueError(f"Config file not found: {path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Config file {path} is not valid YAML: {e}")

    if not data:
        raise ValueError(f"Config file {path} is empty or invalid")

    sites = data.get("sites")
    if not sites:
        raise ValueError("Config must include at least one entry under 'sites'")
    for site in sites:
        for field in ("name", "latitude", "longitude"):
            if field not in site:
                raise ValueError(f"Site entry missing required field '{field}': {site}")
        if not (-90.0 <= site["latitude"] <= 90.0):
            raise ValueError(f"Site '{site['name']}' has invalid latitude {site['latitude']} (must be -90..90)")
        if not (-180.0 <= site["longitude"] <= 180.0):
            raise ValueError(f"Site '{site['name']}' has invalid longitude {site['longitude']} (must be -180..180)")
        site.setdefault("elevation_m", 0.0)

    satellites = data.get("satellites")
    if not satellites:
        raise ValueError("Config must include at least one entry under 'satellites'")
    for sat in satellites:
        if "norad_id" not in sat:
            raise ValueError(f"Satellite entry missing required field 'norad_id': {sat}")
        if not isinstance(sat["norad_id"], int) or sat["norad_id"] <= 0:
            raise ValueError(f"Satellite entry has invalid norad_id: {sat}")

    search = data.get("search") or {}
    search.setdefault("start", "now")
    search.setdefault("hours", 48)
    if search["hours"] <= 0:
        raise ValueError(f"search.hours must be positive, got {search['hours']}")

    elevation_mask_deg = data.get("elevation_mask_deg", 0.0)

    output = data.get("output")
    if output is not None:
        if "path" not in output:
            raise ValueError(f"'output' section requires a 'path' field: {output}")
        output.setdefault("format", None)  # inferred from path extension if not given

    return {
        "sites": sites,
        "satellites": satellites,
        "search": search,
        "elevation_mask_deg": elevation_mask_deg,
        "output": output,
    }
