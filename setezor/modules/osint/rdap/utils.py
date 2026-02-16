from setezor.models.rdap_model import RdapDomain, RdapIpnetwork

def extract_events(events) -> dict:
    if not events:
        return {}
    result = {}
    for ev in events.root:
        if ev.eventAction:
            key = str(ev.eventAction).replace(" ", "_")
            result[key] = ev.eventDate.root if ev.eventDate else None
    return result

def extract_from_entity(entity) -> dict:
    result = {}

    if entity.handle:
        result["handle"] = str(entity.handle)

    result.update(extract_events(entity.events))

    if entity.vcardArray and isinstance(entity.vcardArray.root, list) and len(entity.vcardArray.root) == 2:
        vcard = entity.vcardArray.root
        names_by_lang = {}
        org = None
        email = None
        phone = None
        kind = None
        country = None
        full_address = ""

        for field in vcard[1]:
            if not isinstance(field, list) or len(field) < 4:
                continue
            key = field[0]
            params = field[1] if isinstance(field[1], dict) else {}
            value = field[3]

            def to_str(val):
                if isinstance(val, str):
                    return val
                elif isinstance(val, list):
                    return str(val[0]) if val else ""
                else:
                    return str(val)
                
            if key == "fn":
                lang = params.get("language") or "default"
                names_by_lang[lang] = to_str(value)
            elif key == "org":
                org = to_str(value)
            elif key == "email":
                email = to_str(value)
            elif key == "tel":
                phone = to_str(value)
            elif key == "kind":
                kind = to_str(value)
            elif key == "adr" and isinstance(value, list) and len(value) >= 7:
                pobox, ext, street, city, region, postcode, country_in_adr = (value + [""] * 7)[:7]
                parts = [to_str(x).strip() for x in [street, city, region, postcode] if to_str(x).strip()]
                full_address = ", ".join(parts)

                country_val = None
                if country_in_adr.strip():
                    country_val = country_in_adr.strip()
                elif isinstance(params, dict) and "cc" in params:
                    country_val = str(params["cc"]).strip()

                if country_val:
                    full_address += ", " + country_val
                    country = country_val

                if full_address:
                    result["address"] = full_address
                    if country_val:
                        result["country"] = country_val

            elif key == "adr" and isinstance(params, dict) and "label" in params:
                label = params["label"]
                if label and not full_address:
                    result["address"] = label.replace("\n", ", ")

        if names_by_lang:
            result["name"] = names_by_lang
        if org:
            result["org"] = org
        if email:
            result["email"] = email
        if phone:
            result["phone"] = phone
        if kind:
            result["kind"] = kind
        if country:
            result["country"] = country

    if entity.publicIds:
        for pid in entity.publicIds.root:
            if pid.type == "Taxpayer ID":
                result["taxpayer_id"] = pid.identifier
                break

    return result

def extract_entities(entities) -> dict:
    if not entities:
        return {}

    entities_by_role = {}

    def process(ent):
        simplified = extract_from_entity(ent)
        roles = ent.roles or []
        should_include = bool(simplified) or (ent.entities and len(ent.entities) > 0)
        if should_include:
            for role in roles:
                role_key = str(role.value) if hasattr(role, 'value') else str(role)
                entities_by_role.setdefault(role_key, []).append(simplified or {})
        if ent.entities:
            for nested in ent.entities:
                process(nested)

    for ent in entities:
        process(ent)

    return entities_by_role




def simplify_rdap_domain(domain: RdapDomain) -> dict:
    res = {
        "handle": domain.handle,
        "ldhName": domain.ldhName.root if domain.ldhName else None,
        "status": domain.status.root if domain.status else None,
    }
    res.update(extract_events(domain.events))

    if domain.nameservers:
        nameservers = []
        for ns in domain.nameservers:
            ns_entry = {"ldhName": ns.ldhName.root}
            if ns.ipAddresses:
                ip_addrs = {}
                if ns.ipAddresses.v4:
                    ip_addrs["v4"] = [str(ip.root) for ip in ns.ipAddresses.v4]
                if ns.ipAddresses.v6:
                    ip_addrs["v6"] = [str(ip.root) for ip in ns.ipAddresses.v6]
                if ip_addrs:
                    ns_entry["ipAddresses"] = ip_addrs
            nameservers.append(ns_entry)
        res["nameservers"] = nameservers

    entities = extract_entities(domain.entities)
    if entities:
        res["entities"] = entities

    return res

def simplify_rdap_ipnetwork(ipnet: RdapIpnetwork) -> dict:
    res = {
        "handle": ipnet.handle,
        "ipVersion": ipnet.ipVersion.value if ipnet.ipVersion else None,
        "name": ipnet.name,
        "type": ipnet.type.root if ipnet.type else None,
        "country": ipnet.country.root if ipnet.country else None,
        "nicbr_autnum": ipnet.nicbr_autnum if ipnet.nicbr_autnum else None,
        "startAddress": str(ipnet.startAddress.root.root) if ipnet.startAddress else None,
        "endAddress": str(ipnet.endAddress.root.root) if ipnet.endAddress else None,
    }
    res.update(extract_events(ipnet.events))

    entities = extract_entities(ipnet.entities)
    if entities:
        res["entities"] = entities

    return res