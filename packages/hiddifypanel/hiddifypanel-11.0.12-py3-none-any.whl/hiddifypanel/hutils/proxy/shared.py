from collections import defaultdict
import ipaddress
from flask import current_app, request, g
import glob
import random
import re
import json
from ipaddress import IPv4Address, IPv6Address
from hiddifypanel.cache import cache
from hiddifypanel.models import Proxy, ProxyProto, ProxyL3, ProxyTransport, ProxyCDN, Domain, DomainType, ConfigEnum, hconfig, get_hconfigs
from hiddifypanel import hutils


def get_ssh_hostkeys(hconfigs, dojson=False) -> list[str] | str:
    host_keys = [
        # hconfigs[ConfigEnum.ssh_host_dsa_pub],
        hconfigs[ConfigEnum.ssh_host_ed25519_pub],
        hconfigs[ConfigEnum.ssh_host_ecdsa_pub],
        hconfigs[ConfigEnum.ssh_host_rsa_pub],
    ]
    if dojson:
        return json.dumps(host_keys)
    return host_keys


def is_proxy_valid(proxy: Proxy, domain_db: Domain, port: int) -> dict | None:
    name = proxy.name
    l3 = proxy.l3
    if not port:
        return {'name': name, 'msg': "port not defined", 'type': 'error', 'proto': proxy.proto}
    if "reality" not in l3 and 'reality' in domain_db.mode:
        return {'name': name, 'msg': "1reality proxy not in reality domain", 'type': 'debug', 'proto': proxy.proto}

    if "reality" in l3 and 'reality' not in domain_db.mode:
        return {'name': name, 'msg': "2reality proxy not in reality domain", 'type': 'debug', 'proto': proxy.proto}

    for p in ['tcp','grpc','xhttp']:
        if "reality" in l3 and p in domain_db.mode  and p not in proxy.transport:
            return {'name': name, 'msg': f"reality proxy {proxy.transport} in reality {p} domain", 'type': 'debug', 'proto': proxy.proto}
        if "reality" in l3 and p not in domain_db.mode  and p in proxy.transport:
            return {'name': name, 'msg': f"reality {p} proxy not in reality {p} domain", 'type': 'debug', 'proto': proxy.proto}


    is_cdn = ProxyCDN.CDN == proxy.cdn or ProxyCDN.Fake == proxy.cdn
    if is_cdn and domain_db.mode not in [DomainType.cdn, DomainType.auto_cdn_ip, DomainType.worker]:
        # print("cdn proxy not in cdn domain", domain, name)
        return {'name': name, 'msg': "cdn proxy not in cdn domain", 'type': 'debug', 'proto': proxy.proto}

    if not is_cdn and domain_db.mode in [DomainType.cdn, DomainType.auto_cdn_ip, DomainType.worker]:
        # print("not cdn proxy  in cdn domain", domain, name, proxy.cdn)
        return {'name': name, 'msg': "not cdn proxy  in cdn domain", 'type': 'debug', 'proto': proxy.proto}

    if proxy.cdn == ProxyCDN.relay and domain_db.mode not in [DomainType.relay]:
        return {'name': name, 'msg': "relay proxy not in relay domain", 'type': 'debug', 'proto': proxy.proto}

    if proxy.cdn != ProxyCDN.relay and domain_db.mode in [DomainType.relay]:
        return {'name': name, 'msg': "relay proxy not in relay domain", 'type': 'debug', 'proto': proxy.proto}

    if domain_db.mode == DomainType.worker and proxy.transport == ProxyTransport.grpc:
        return {'name': name, 'msg': "worker does not support grpc", 'type': 'debug', 'proto': proxy.proto}

    if domain_db.mode == DomainType.old_xtls_direct:
        return {'name': name, 'msg': "unsupported", 'type': 'debug', 'proto': proxy.proto}
    # if domain_db.mode != DomainType.old_xtls_direct and "tls" in proxy.l3 and proxy.cdn == ProxyCDN.direct and proxy.transport in [ProxyTransport.tcp, ProxyTransport.XTLS]:
        # return {'name': name, 'msg': "only  old_xtls_direct  support this", 'type': 'debug', 'proto': proxy.proto}

    if proxy.proto == "trojan" and not is_tls(l3):
        return {'name': name, 'msg': "trojan but not tls", 'type': 'warning', 'proto': proxy.proto}

    # if l3 == "http" and ProxyTransport.XTLS in proxy.transport:
    #     return {'name': name, 'msg': "http and xtls???", 'type': 'warning', 'proto': proxy.proto}

    if l3 == "http" and proxy.proto in [ProxyProto.ss, ProxyProto.ssr]:
        return {'name': name, 'msg': "http and ss or ssr???", 'type': 'warning', 'proto': proxy.proto}

    return 


def get_port(proxy: Proxy, hconfigs: dict, domain_db: Domain, ptls: int, phttp: int, pport: int | None) -> int:
    l3 = proxy.l3
    port = 443
    if isinstance(phttp, str):
        phttp = int(phttp) if phttp != "None" else None  # type: ignore
    if isinstance(ptls, str):
        ptls = int(ptls) if ptls != "None" else None  # type: ignore
    if l3 == "kcp":
        port = hconfigs[ConfigEnum.kcp_ports].split(",")[0]
    elif proxy.proto == ProxyProto.wireguard:
        port = hconfigs[ConfigEnum.wireguard_port]
    elif proxy.proto == "tuic":
        port = domain_db.internal_port_tuic
    elif proxy.proto == "hysteria2":
        port = domain_db.internal_port_hysteria2
    elif l3 == 'ssh':
        port = hconfigs[ConfigEnum.ssh_server_port]
    elif is_tls(l3):
        port = ptls
    elif l3 == "http":
        port = phttp
    else:
        port = int(pport)  # type: ignore
    return port


def is_tls(l3) -> bool:

    return 'tls' in l3 or "reality" in l3 or l3 in [ProxyL3.h3_quic]


@cache.cache(ttl=300)
def get_proxies(child_id: int = 0, only_enabled=False) -> list['Proxy']:
    proxies = Proxy.query.filter(Proxy.child_id == child_id).all()
    proxies = [c for c in proxies if 'restls' not in c.transport]

    if not hconfig(ConfigEnum.tuic_enable, child_id):
        proxies = [c for c in proxies if c.proto != ProxyProto.tuic]
    if not hconfig(ConfigEnum.wireguard_enable, child_id):
        proxies = [c for c in proxies if c.proto != ProxyProto.wireguard]
    if not hconfig(ConfigEnum.ssh_server_enable, child_id):
        proxies = [c for c in proxies if c.proto != ProxyProto.ssh]
    if not hconfig(ConfigEnum.hysteria_enable, child_id):
        proxies = [c for c in proxies if c.proto != ProxyProto.hysteria2]
    if not hconfig(ConfigEnum.shadowsocks2022_enable, child_id):
        proxies = [c for c in proxies if 'shadowsocks' != c.transport]

    if not hconfig(ConfigEnum.ssfaketls_enable, child_id):
        proxies = [c for c in proxies if 'faketls' != c.transport]
    if not hconfig(ConfigEnum.v2ray_enable, child_id):
        proxies = [c for c in proxies if 'v2ray' != c.proto]
    if not hconfig(ConfigEnum.shadowtls_enable, child_id):
        proxies = [c for c in proxies if c.transport != 'shadowtls']
    if not hconfig(ConfigEnum.ssr_enable, child_id):
        proxies = [c for c in proxies if 'ssr' != c.proto]
    if not hconfig(ConfigEnum.vmess_enable, child_id):
        proxies = [c for c in proxies if 'vmess' not in c.proto]
    if not hconfig(ConfigEnum.vless_enable, child_id):
        proxies = [c for c in proxies if 'vless' not in c.proto or 'reality' in c.l3]
    if not hconfig(ConfigEnum.trojan_enable, child_id):
        proxies = [c for c in proxies if 'trojan' not in c.proto]
    if not hconfig(ConfigEnum.httpupgrade_enable, child_id):
        proxies = [c for c in proxies if ProxyTransport.httpupgrade not in c.transport]
    if not hconfig(ConfigEnum.xhttp_enable, child_id):
        proxies = [c for c in proxies if ProxyTransport.xhttp not in c.transport]
    if not hconfig(ConfigEnum.ws_enable, child_id):
        proxies = [c for c in proxies if ProxyTransport.WS not in c.transport]
    # if not hconfig(ConfigEnum.xtls_enable, child_id):
        #     proxies = [c for c in proxies if ProxyTransport.XTLS not in c.transport]
    if not hconfig(ConfigEnum.grpc_enable, child_id):
        proxies = [c for c in proxies if ProxyTransport.grpc not in c.transport]
    if not hconfig(ConfigEnum.tcp_enable, child_id):
        proxies = [c for c in proxies if 'tcp' not in c.transport]
    if not hconfig(ConfigEnum.h2_enable, child_id):
        proxies = [c for c in proxies if 'h2' not in c.transport and c.l3 not in [ProxyL3.tls_h2_h1, ProxyL3.tls_h2]]
    if not hconfig(ConfigEnum.kcp_enable, child_id):
        proxies = [c for c in proxies if 'kcp' not in c.l3]
    if not hconfig(ConfigEnum.reality_enable, child_id):
        proxies = [c for c in proxies if 'reality' not in c.l3]
    if not hconfig(ConfigEnum.quic_enable, child_id):
        proxies = [c for c in proxies if 'h3_quic' not in c.l3]
    if not hconfig(ConfigEnum.http_proxy_enable, child_id):
        proxies = [c for c in proxies if 'http' != c.l3]

    if not Domain.query.filter(Domain.mode.in_([DomainType.cdn, DomainType.auto_cdn_ip])).first():
        proxies = [c for c in proxies if c.cdn != "CDN"]

    if not Domain.query.filter(Domain.mode.in_([DomainType.relay])).first():
        proxies = [c for c in proxies if c.cdn != ProxyCDN.relay]

    if not Domain.query.filter(Domain.mode.in_([DomainType.cdn, DomainType.auto_cdn_ip]), Domain.servernames != "", Domain.servernames != Domain.domain).first():
        proxies = [c for c in proxies if 'Fake' not in c.cdn]

    # proxies = [c for c in proxies if not ('vless' == c.proto and ProxyTransport.tcp == c.transport and c.cdn == ProxyCDN.direct)]

    if only_enabled:
        proxies = [p for p in proxies if p.enable]
    return proxies


def get_valid_proxies(domains: list[Domain]) -> list[dict]:
    allp = []
    allphttp = [p for p in request.args.get("phttp", "").split(',') if p]
    allptls = [p for p in request.args.get("ptls", "").split(',') if p]
    added_ip = defaultdict(set)
    configsmap = {}
    proxeismap = {}
    for domain in domains:
        if domain.child_id not in configsmap:
            configsmap[domain.child_id] = get_hconfigs(domain.child_id)
            proxeismap[domain.child_id] = get_proxies(domain.child_id, only_enabled=True)
            # print(proxeismap[domain.child_id])
        hconfigs = configsmap[domain.child_id]
        ips = domain.get_cdn_ips_parsed()
        if not ips:
            ips = hutils.network.get_domain_ips_cached(domain.domain)
        for proxy in proxeismap[domain.child_id]:
            noDomainProxies = False
            if proxy.proto in [ProxyProto.ssh, ProxyProto.wireguard]:
                noDomainProxies = True
            if proxy.proto in [ProxyProto.ss] and proxy.transport not in [ProxyTransport.grpc, ProxyTransport.h2, ProxyTransport.WS, ProxyTransport.httpupgrade, ProxyTransport.xhttp]:
                noDomainProxies = True
            options = []
            key = f'{proxy.proto}{proxy.transport}{proxy.cdn}{proxy.l3}'

            if proxy.proto in [ProxyProto.ssh, ProxyProto.tuic, ProxyProto.hysteria2, ProxyProto.wireguard, ProxyProto.ss]:
                if noDomainProxies and all([x in added_ip[key] for x in ips]):
                    continue

                for x in ips:
                    added_ip[key].add(x)

                if proxy.proto in [ProxyProto.ssh, ProxyProto.wireguard, ProxyProto.ss]:
                    # if domain.mode == 'fake':
                    #     continue
                    if proxy.proto in [ProxyProto.ssh]:
                        options = [{'pport': hconfigs[ConfigEnum.ssh_server_port]}]
                    elif proxy.proto in [ProxyProto.wireguard]:
                        options = [{'pport': hconfigs[ConfigEnum.wireguard_port]}]
                    elif proxy.transport in [ProxyTransport.shadowsocks]:
                        options = [{'pport': hconfigs[ConfigEnum.shadowsocks2022_port]}]
                    elif proxy.proto in [ProxyProto.ss]:
                        options = [{'pport': 443}]
                elif proxy.proto == ProxyProto.tuic:
                    options = [{'pport': hconfigs[ConfigEnum.tuic_port]}]
                elif proxy.proto == ProxyProto.hysteria2:
                    options = [{'pport': hconfigs[ConfigEnum.hysteria_port]}]
            else:
                protos = ['http', 'tls'] if hconfigs.get(ConfigEnum.http_proxy_enable) else ['tls']
                for t in protos:
                    for port in hconfigs[ConfigEnum.http_ports if t == 'http' else ConfigEnum.tls_ports].split(','):
                        phttp = port if t == 'http' else None
                        ptls = port if t == 'tls' else None
                        if phttp and len(allphttp) and phttp not in allphttp:
                            continue
                        if ptls and len(allptls) and ptls not in allptls:
                            continue
                        options.append({'phttp': phttp, 'ptls': ptls})

            for opt in options:
                pinfo = make_proxy(hconfigs, proxy, domain, **opt)
                # if key in "vlesstcp":
                #     print(pinfo)
                if 'msg' not in pinfo:
                    allp.append(pinfo)
    return allp


def random_or_none(inp: list):
    if not inp:
        return
    return random.sample(list(inp), 1)[0]


split_pattern = re.compile(r'[ \t\r\n;,]+')


def sni_host_server_extractor(domain_db: Domain, hconfigs):
    
    server=sni=host = domain_db.domain.replace("*", hutils.random.get_random_string(5, 15))
    is_cdn = domain_db.mode in [DomainType.cdn, DomainType.auto_cdn_ip]
    if auto_ip:=domain_db.auto_cdn_ip():
        server=auto_ip[0]
    elif 'special' in domain_db.mode.value or domain_db.mode in [DomainType.fake]:
        server=hutils.network.get_direct_host_or_ip(4)
    
    if domain_db.resolve_ip:
        server = str(random_or_none(hutils.network.get_domain_ips_cached(server)) or server)

    
    allow_insecure=not domain_db.need_valid_ssl
    if all_snis := split_pattern.split((domain_db.servernames or "").strip()):
        sni = random_or_none(all_snis) or sni
        if 'reality' in domain_db.mode:
            allow_insecure=False
            if hconfigs[ConfigEnum.core_type] == "singbox": #TODO
                sni = all_snis[0]
            
        else: 
            allow_insecure=True
    

    base = {
        'sni': sni,
        'host': host,
        'server': server,
        'mode': domain_db.mode,
        'allow_insecure': allow_insecure,
        'cdn': is_cdn,
    }
    if 'reality' in domain_db.mode:
        base['reality_short_id'] = random.sample(hconfigs[ConfigEnum.reality_short_ids].split(','), 1)[0]
        # base['flow']="xtls-rprx-vision"
        base['reality_pbk'] = hconfigs[ConfigEnum.reality_public_key]
        # del base['host']

        # if not domain_db.cdn_ip:
        #     base['server']=hiddify.get_domain_ip(base['server'])

    return base

def put_default_header(params:dict):
    if not isinstance(params.get('headers'),dict):
        params['headers']={}
        
    if not params['headers'].get('User-Agent'):
        params['headers']['User-Agent']=hconfig(ConfigEnum.default_useragent_string)
    if not params['headers'].get('Pragma'):
        params['headers']['Pragma']="no-cache"
    


def make_proxy(hconfigs: dict, proxy: Proxy, domain_db: Domain, phttp=80, ptls=443, pport: int | None = None) -> dict:

    l3 = proxy.l3
    domain = domain_db.domain
    child_id = domain_db.child_id
    name = proxy.name
    port = hutils.proxy.get_port(proxy, hconfigs, domain_db, ptls, phttp, pport)

    if val_res := hutils.proxy.is_proxy_valid(proxy, domain_db, port):
        # print(f'{name}:{domain}->{val_res}')
        return val_res

    if 'reality' in proxy.l3:
        alpn = "h2" if proxy.transport in ['h2', "grpc"] else 'http/1.1'
    else:
        alpn = "h2" if proxy.l3 in ['tls_h2'] or proxy.transport in ["grpc", 'h2'] else 'h2,http/1.1' if proxy.l3 == 'tls_h2_h1' else "http/1.1"
        if proxy.l3 in [ProxyL3.h3_quic]:
            alpn = "h3"

    # cdn_forced_host = domain_db.cdn_ip or (domain_db.domain if domain_db.mode != DomainType.reality else hutils.network.get_direct_host_or_ip(4))
    # is_cdn = ProxyCDN.CDN == proxy.cdn or ProxyCDN.Fake == proxy.cdn
    domain_data=sni_host_server_extractor(domain_db, hconfigs)
    base = {
        **domain_data,
        'name': name,
        # 'cdn': is_cdn,
        # 'mode': "CDN" if is_cdn else "direct",
        'l3': l3,
        
        'port': port,
        
        'uuid': str(g.account.uuid),
        'proto': proxy.proto,
        'transport': proxy.transport,
        'proxy_path': hconfigs[ConfigEnum.proxy_path],
        'alpn': alpn,
        'extra_info': f'{domain_db.alias or domain_db.domain}',
        'fingerprint': hconfigs[ConfigEnum.utls],
        # 'allow_insecure': domain_db.mode == DomainType.fake or "Fake" in proxy.cdn,
        'dbe': proxy,
        'dbdomain': domain_db,
        'params': proxy.params or {},
    }
    put_default_header(base['params'])

    
    if domain_db.download_domain:
        base['download'] = sni_host_server_extractor(domain_db.download_domain,hconfigs)
    else:
        base['download']=domain_data
        
    if 'download' not in base['params']:
        base['params']['download']={}
    base['download']['params']=base['params']['download']
    put_default_header(base['download']['params'])

    base['download']['alpn']=base['params']['download'].get('alpn',alpn)

        

            
    if proxy.proto in ['tuic', 'hysteria2']:
        base['alpn'] = "h3"
        if proxy.proto == 'hysteria2':
            base['hysteria_up_mbps'] = hconfigs.get(ConfigEnum.hysteria_up_mbps)
            base['hysteria_down_mbps'] = hconfigs.get(ConfigEnum.hysteria_down_mbps)
            base['hysteria_obfs_enable'] = hconfigs.get(ConfigEnum.hysteria_obfs_enable)
            base['hysteria_obfs_password'] = hconfigs.get(ConfigEnum.proxy_path)  # TODO: it should not be correct
        return base
    if proxy.proto in ['wireguard']:
        base['wg_pub'] = g.account.wg_pub
        base['wg_pk'] = g.account.wg_pk
        base['wg_psk'] = g.account.wg_psk
        base['wg_ipv4'] = hutils.network.add_number_to_ipv4(hconfigs[ConfigEnum.wireguard_ipv4], g.account.id)
        base['wg_ipv6'] = hutils.network.add_number_to_ipv6(hconfigs[ConfigEnum.wireguard_ipv6], g.account.id)
        base['wg_server_pub'] = hconfigs[ConfigEnum.wireguard_public_key]
        base['wg_noise_trick'] = hconfigs[ConfigEnum.wireguard_noise_trick]
        return base

    if proxy.proto in [ProxyProto.vmess]:
        base['cipher'] = "auto"  # "chacha20-poly1305"

    
    if l3 == "http" and not hconfigs[ConfigEnum.http_proxy_enable]:
        return {'name': name, 'msg': "http but http is disabled ", 'type': 'debug', 'proto': proxy.proto}

    path = {
        'vless': f'{hconfigs[ConfigEnum.path_vless]}',
        'trojan': f'{hconfigs[ConfigEnum.path_trojan]}',
        'vmess': f'{hconfigs[ConfigEnum.path_vmess]}',
        'ss': f'{hconfigs[ConfigEnum.path_ss]}',
        'v2ray': f'{hconfigs[ConfigEnum.path_ss]}'
    }

    if base["proto"] in ['v2ray', 'ss', 'ssr']:
        base['cipher'] = hconfigs[ConfigEnum.shadowsocks2022_method]
        base['password'] = f'{hutils.encode.do_base_64(hconfigs[ConfigEnum.shared_secret].replace("-",""))}:{hutils.encode.do_base_64(g.account.uuid.replace("-",""))}'

    if base['proto'] == 'trojan':
        base['password'] = base['uuid']
    if base["proto"] == "ssr":
        base["ssr-obfs"] = "tls1.2_ticket_auth"
        base["ssr-protocol"] = "auth_sha1_v4"
        base["fakedomain"] = hconfigs[ConfigEnum.ssr_fakedomain]
        base["mode"] = "FakeTLS"
        return base
    elif "faketls" in proxy.transport:
        base['fakedomain'] = hconfigs[ConfigEnum.ssfaketls_fakedomain]
        base['mode'] = 'FakeTLS'
        return base
    elif "shadowtls" in proxy.transport:
        base['fakedomain'] = hconfigs[ConfigEnum.shadowtls_fakedomain]
        # base['sni'] = hconfigs[ConfigEnum.shadowtls_fakedomain]
        base['shared_secret'] = hconfigs[ConfigEnum.shared_secret]
        base['mode'] = 'ShadowTLS'
        return base
    elif "shadowsocks" in proxy.transport:
        return base
    if proxy.l3 in [ProxyL3.reality] and proxy.transport in [ProxyTransport.tcp]:
        base['flow'] = 'xtls-rprx-vision'
        return {**base, 'transport': 'tcp'}

    if proxy.proto in {'vless', 'trojan', 'vmess'} and hconfigs.get(ConfigEnum.mux_enable):
        if hconfigs[ConfigEnum.mux_enable]:
            base['mux_enable'] = hconfigs[ConfigEnum.core_type]

            base['mux_protocol'] = hconfigs.get(ConfigEnum.mux_protocol, "h2mux")
            base['mux_max_connections'] = hconfigs.get(ConfigEnum.mux_max_connections, 0)
            base['mux_min_streams'] = hconfigs.get(ConfigEnum.mux_min_streams, 0)
            base['mux_max_streams'] = hconfigs.get(ConfigEnum.mux_max_streams, 0)
            base['mux_padding_enable'] = hconfigs.get(ConfigEnum.mux_padding_enable)

            if hconfigs[ConfigEnum.mux_brutal_enable]:
                base['mux_brutal_enable'] = True
                base['mux_brutal_up_mbps'] = hconfigs.get(ConfigEnum.mux_brutal_up_mbps, 10)
                base['mux_brutal_down_mbps'] = hconfigs.get(ConfigEnum.mux_brutal_down_mbps, 10)

    if base['cdn'] and proxy.proto in {'vless', 'trojan', "vmess"}:
        if hconfigs[ConfigEnum.tls_fragment_enable] and "tls" in base["l3"]:
            base["tls_fragment_enable"] = True
            base["tls_fragment_size"] = hconfigs[ConfigEnum.tls_fragment_size]
            base["tls_fragment_sleep"] = hconfigs[ConfigEnum.tls_fragment_sleep]

        if hconfigs[ConfigEnum.tls_mixed_case]:
            base["tls_mixed_case"] = hconfigs[ConfigEnum.tls_mixed_case]
            base['host'] = hutils.random.random_case(base['host'])
            base['sni'] = hutils.random.random_case(base['sni'])
            base['server'] = hutils.random.random_case(base['server'])
            if base.get('fakedomain'):
                base['fakedomain'] = hutils.random.random_case(base['fakedomain'])

        if hconfigs[ConfigEnum.tls_padding_enable]:
            base["tls_padding_enable"] = hconfigs[ConfigEnum.tls_padding_enable]
            base["tls_padding_length"] = hconfigs[ConfigEnum.tls_padding_length]

    if "tcp" in proxy.transport:
        base['transport'] = 'tcp'
        base['path'] = f'/{path[base["proto"]]}{hconfigs[ConfigEnum.path_tcp]}'
        return base
    
    if proxy.transport in ["ws", "WS"]:
        base['transport'] = 'ws'
        base['path'] = f'/{path[base["proto"]]}{hconfigs[ConfigEnum.path_ws]}'
        
        return base

    if proxy.transport in [ProxyTransport.httpupgrade]:
        base['transport'] = 'httpupgrade'
        base['path'] = f'/{path[base["proto"]]}{hconfigs[ConfigEnum.path_httpupgrade]}'
        
        return base
    
    if proxy.transport in [ProxyTransport.xhttp]:
        base['transport'] = 'xhttp'
        base['path'] = f'/{path[base["proto"]]}{hconfigs[ConfigEnum.path_xhttp]}'
        base['xhttp_mode']=base['params'].get('mode',"auto")
        if dl:=base.get('download'):
            dl['path']=base['path']
            dl['xhttp_mode']=dl['params'].get('mode',"auto")

            if all_element_in_first_dict_is_exist_in_second(dl,base):
                del base['download']
        return base

    if proxy.transport == "grpc":
        base['transport'] = 'grpc'
        # base['grpc_mode'] = "multi" if hconfigs[ConfigEnum.core_type]=='xray' else 'gun'
        base['grpc_mode'] = 'gun'
        base['grpc_service_name'] = f'{path[base["proto"]]}{hconfigs[ConfigEnum.path_grpc]}'
        base['path'] = base['grpc_service_name']
        return base

    if "h1" in proxy.transport:
        base['transport'] = 'tcp'
        base['alpn'] = 'http/1.1'
        return base
    if ProxyProto.ssh == proxy.proto:
        base['private_key'] = g.account.ed25519_private_key
        base['host_keys'] = hutils.proxy.get_ssh_hostkeys(hconfigs, False)
        # base['ssh_port'] = hconfig(ConfigEnum.ssh_server_port)
        return base
    return {'name': name, 'msg': 'not valid', 'type': 'error', 'proto': proxy.proto}

def all_element_in_first_dict_is_exist_in_second(fdict,sdict):
    for k,v in fdict.items():
        if k=="params":
            continue
        if isinstance(v,dict):
            if not all_element_in_first_dict_is_exist_in_second(v,sdict.get(k,{})):
                return False
        if sdict.get(k,v)!=v:
            return False
        
    return True

class ProxyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, IPv4Address) or isinstance(obj, IPv6Address):
            return str(obj)
        return super().default(obj)
