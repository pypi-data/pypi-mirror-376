import ipaddress
from hiddifypanel.auth import login_required, current_account

from hiddifypanel.models import *
import re
from flask import g  # type: ignore
from markupsafe import Markup

from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from hiddifypanel.panel.run_commander import Command, commander
from wtforms.validators import Regexp, ValidationError

from hiddifypanel.models import *
from hiddifypanel.panel import hiddify, custom_widgets
from .adminlte import AdminLTEModelView
from hiddifypanel import hutils

from loguru import logger
from flask import current_app
# Define a custom field type for the related domains


# class ConfigDomainsField(SelectField):
#     def __init__(self, label=None, validators=None,*args, **kwargs):
#         kwargs.pop("allow_blank")
#         super().__init__(label, validators,*args, **kwargs)
#         self.choices=[(d.id,d.domain) for d in Doamin.query.filter(Domain.sub_link_only!=True).all()]


class DomainAdmin(AdminLTEModelView):
    # edit_modal = False
    # create_modal = False
    column_hide_backrefs = False

    list_template = 'model/domain_list.html'
    # edit_modal = True
    form_overrides = {'mode': custom_widgets.EnumSelectField}
    form_widget_args = {
        'description': {
            'rows': 100,
            'style': 'font-family: monospace; direction:ltr'
        }
    }
    column_descriptions = dict(
        domain=_("domain.description"),
        mode=_("Direct mode means you want to use your server directly (for usual use), CDN means that you use your server on behind of a CDN provider."),
        cdn_ip=_("config.cdn_forced_host.description"),
        show_domains=_('domain.show_domains_description'),
        alias=_('The name shown in the configs for this domain.'),
        servernames=_('config.reality_server_names.description'),
        sub_link_only=_('This can be used for giving your users a permanent non blockable links.'),
        grpc=_('grpc-proxy.description'),
        download_domain=_('download_domain.description'),
        resolve_ip=_("domain.resolveip.description")
    )
    # create_modal = True
    can_export = False
    form_widget_args = {'show_domains': {'class': 'form-control ltr'},'download_domain': {'class': 'form-control ltr'}}

    form_args = {
        'mode': {'enum': DomainType},
        'show_domains': {
            'query_factory': lambda: Domain.query.filter(     Domain.sub_link_only == False),
        },
        'domain': {
            'validators': [
                Regexp(r'^(\*\.)?([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,})$|^$',message=__("Should be a valid domain"))]},
        "cdn_ip": {
            'validators': [
                Regexp(r"(((((25[0-5]|(2[0-4]|1\d|[1-9]|)\d).){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d))|^([A-Za-z0-9\-\.]+\.[a-zA-Z]{2,}))[ \t\n,;]*\w{3}[ \t\n,;]*)*",message=__("Invalid IP or domain"))]},
        "servernames": {
            'validators': [
                Regexp(r"^([\w-]+\.)+[\w-]+(,\s*([\w-]+\.)+[\w-]+)*$",re.IGNORECASE,_("Invalid REALITY hostnames"))]}}
    column_list = ["domain", "alias", "mode", "domain_ip", "show_domains"]
    column_editable_list = ["alias"]
    # column_filters=["domain","mode"]
    # form_excluded_columns=['work_with']
    column_searchable_list = ["domain", "mode"]
    column_labels = {
        "domain": _("domain.domain"),
        'sub_link_only': _('Only for sublink?'),
        "mode": _("domain.mode"),
        "cdn_ip": _("config.cdn_forced_host.label"),
        'domain_ip': _('domain.ip'),
        'servernames': _('config.reality_server_names.label'),
        'show_domains': _('Show Domains'),
        'alias': _('Alias'),
        'grpc': _('gRPC'),
        "download_domain":_('download_domain.label'),
        'resolve_ip':_("domain.resolveip.label"),
    }

    form_columns = ['mode', 'domain', 'alias', 'servernames', 'cdn_ip', 'resolve_ip', 'show_domains', 'download_domain',]

    def _domain_admin_link(view, context, model, name):
        if model.mode == DomainType.fake:
            return Markup(f"<span class='badge'>{model.domain}</span>")
        d = model.domain
        if "*" in d:
            d = d.replace("*", hutils.random.get_random_string(5, 15))
        admin_link = hiddify.get_account_panel_link(g.account, d)
        return Markup(
            f'<div class="btn-group"><a href="{admin_link}" class="btn btn-xs btn-secondary">' + _("admin link") +
            f'</a><a href="{admin_link}" class="btn btn-xs btn-info ltr" target="_blank">{model.domain}</a></div>')

    def _domain_ip(view, context, model, name):
        dips = hutils.network.get_domain_ips_cached(model.domain)
        # The get_domain_ip function uses the socket library, which relies on the system DNS resolver. So it may sometimes use cached data, which is not desirable
        # if not dips:
        #     dip = hutils.network.resolve_domain_with_api(model.domain)
        myips = set(hutils.network.get_ips())
        all_res = ""
        for dip in dips:
            if dip in myips and model.mode in [DomainType.direct, DomainType.sub_link_only]:
                badge_type = ''
            elif dip and dip not in myips and model.mode != DomainType.direct:
                badge_type = 'warning'
            else:
                badge_type = 'danger'
            res = f'<span class="badge badge-{badge_type}">{dip}</span>'
            if model.sub_link_only:
                res += f'<span class="badge badge-success">{_("SubLink")}</span>'
            all_res += res
        return Markup(all_res)

    def _show_domains_formater(view, context, model, name):
        if not len(model.show_domains):
            return _("All")
        else:
            return Markup(" ".join([hiddify.get_domain_btn_link(d) for d in model.show_domains]))

    column_formatters = {
        'domain_ip': _domain_ip,
        'domain': _domain_admin_link,
        'show_domains': _show_domains_formater
    }

    def search_placeholder(self):
        return f"{_('search')} {_('domain.domain')} {_('domain.mode')}"

    # def on_form_prefill(self, form, id):
        # Get the Domain object being edited
        # domain = self.session.query(Domain).get(id)

        # Pre-select the related domains in the checkbox list
        # form.show_domains = [d.id for d in Domain.query.all()]

    # TODO: refactor this function
    def on_model_change(self, form, model, is_created):
        # Sanitize domain input
        model.domain = (model.domain or '').lower().strip()
        if model.download_domain and model.domain==model.download_domain.domain:
            model.download_domain_id=None
            model.download_domain=None
        # Basic validation
        if model.domain == '' and model.mode != DomainType.fake:
            raise ValidationError(_("domain.empty.allowed_for_fake_only"))

        self._validate_not_used_before(model,is_created)
        ipv4_list = hutils.network.get_ips(4)
        ipv6_list = hutils.network.get_ips(6)
        server_ips = [*ipv4_list, *ipv6_list]

        if not server_ips:
            raise ValidationError(_("Couldn't find your ip addresses"))

        # Validate domain based on mode
        if "*" in model.domain and model.mode not in [DomainType.cdn, DomainType.auto_cdn_ip]:
            raise ValidationError(_("Domain can not be resolved! there is a problem in your domain"))

        cloudflare_updated=self._update_cloudflare(model, ipv4_list,ipv6_list)
        
        
        self._validate_domain_ips(model, server_ips)

        # Handle CDN IP settings
        if model.mode == DomainType.direct and model.cdn_ip:
            model.cdn_ip = ""
            raise ValidationError(_("Specifying CDN IP is only valid for CDN mode"))
            
        if model.mode == DomainType.fake and not model.cdn_ip:
            model.cdn_ip = str(server_ips[0])
            
        if model.cdn_ip:
            try:
                hutils.network.auto_ip_selector.get_clean_ip(str(model.cdn_ip))
            except Exception:
                raise ValidationError(_("Error in auto cdn format"))
                    
        # Update show domains
        if len(model.show_domains) == Domain.query.count():
            model.show_domains = []
                
        # Handle mode-specific settings
        if model.mode == DomainType.old_xtls_direct and not hconfig(ConfigEnum.xtls_enable):
            set_hconfig(ConfigEnum.xtls_enable, True)
            hutils.proxy.get_proxies().invalidate_all()
        elif "reality" in  model.mode:
            self._validate_reality_settings(model, server_ips)
                
            # Signal config update if needed
        old_db_domain = Domain.by_domain(model.domain)
        if is_created or not old_db_domain or old_db_domain.mode != model.mode:
            # return hiddify.reinstall_action(complete_install=False, domain_changed=True)
            hutils.flask.flash_config_success(restart_mode=ApplyMode.apply_config, domain_changed=True)

            

    def _update_cloudflare(self, model, ipv4_list,ipv6_list):
        if hconfig(ConfigEnum.cloudflare) and model.mode not in [DomainType.fake, DomainType.relay, DomainType.reality]:
            try:
                proxied = model.mode in [DomainType.cdn, DomainType.auto_cdn_ip]
                if ipv4_list:
                    hutils.network.cf_api.add_or_update_dns_record(model.domain, str(ipv4_list[0]), "A", proxied=proxied)
                if ipv6_list:
                    hutils.network.cf_api.add_or_update_dns_record(model.domain, str(ipv6_list[0]), "AAAA", proxied=proxied)
                return True
            except Exception as e:
                raise ValidationError(__("cloudflare.error") + f' {e}')
        return False

    def _validate_reality_settings(self, model, server_ips):
        """Validate REALITY protocol settings with proper error handling"""
        if not hconfig(ConfigEnum.reality_enable):
            set_hconfig(ConfigEnum.reality_enable, True)
            hutils.proxy.get_proxies().invalidate_all()

        model.servernames = (model.servernames or model.domain).lower().strip()
        domains_to_check = set()
        for v in [model.domain, model.servernames]:
            domains_to_check.update(d.strip() for d in v.split(",") if d.strip())

        for d in domains_to_check:
            # Check REALITY compatibility
            if not hutils.network.is_domain_reality_friendly(d):
                raise ValidationError(_("Domain is not REALITY friendly!") + f' {d}')

            try:
                if not hutils.network.is_in_same_asn(d, server_ips[0]):
                    domain_ips = hutils.network.get_domain_ips(d)
                    if domain_ips:
                        dip = next(iter(domain_ips))
                        server_asn = hutils.network.get_ip_asn(server_ips[0])
                        domain_asn = hutils.network.get_ip_asn(dip)
                        msg = _("domain.reality.asn_issue")
                        if server_asn or domain_asn:
                            msg += f"<br> Server ASN={server_asn}<br>{d}_ASN={domain_asn}"
                        hutils.flask.flash(msg, 'warning')
            except Exception as e:
                logger.warning(f"ASN check failed for domain {d}: {str(e)}")

        # Check fallback compatibility
        for d in model.servernames.split(","):
            if d.strip() and not hutils.network.fallback_domain_compatible_with_servernames(model.domain, d):
                msg = _("REALITY Fallback domain is not compatible with server names!") + f' {d} != {model.domain}'
                hutils.flask.flash(msg, 'warning')


    def _validate_not_used_before(self, model,is_created):
        configs = get_hconfigs()
        for c in configs:
            if "domain" in c and c not in [ConfigEnum.decoy_domain, ConfigEnum.reality_fallback_domain] and c.category != 'hidden':
                if model.domain == configs[c]:
                    raise ValidationError(_("You have used this domain in: ") + _(f"config.{c}.label"))

        for td in Domain.query.filter(Domain.mode.in_([DomainType.reality,DomainType.special_reality_xhttp,DomainType.special_reality_grpc,DomainType.special_reality_tcp]), Domain.domain != model.domain).all():
            # print(td)
            if td.servernames and (model.domain in td.servernames.split(",")):
                raise ValidationError(_("You have used this domain in: ") + _(f"config.reality_server_names.label") + td.domain)

        if is_created and Domain.query.filter(Domain.domain == model.domain, Domain.child_id == model.child_id).count() > 1:
            raise ValidationError(_("You have used this domain in: "))

    def _validate_domain_ips(self, model, server_ips):
        """Validate domain IP resolution and matching"""
        
        # Skip validation for wildcard or empty domains
        if (model.domain.startswith('*') or not model.domain) and model.mode not in [DomainType.direct]:
            return True
        if model.mode in [DomainType.fake, DomainType.reality, DomainType.relay]:
            return True
        if "special" in model.mode:
            return True
        # Resolve domain IPs with timeout
        try:
            dips = hutils.network.get_domain_ips(model.domain)
        except Exception as e:
            logger.error(f"Error resolving domain {model.domain}: {str(e)}")
            raise ValidationError(_("Domain cannot be resolved! Please check DNS settings"))
        
        # Validate resolution success
        if not dips:
            raise ValidationError(_("Domain cannot be resolved! Please check DNS settings"))
        
        # Check IP matching based on mode
        domain_ip_matches_server = any(ip in dips for ip in server_ips)
        server_ips_str = ', '.join(map(str, server_ips))
        dips_str = ', '.join(map(str, dips))
    
        if not domain_ip_matches_server and model.mode in [DomainType.direct]:
            raise ValidationError(
                __("Domain IP=%(domain_ip)s is not matched with your ip=%(server_ip)s which is required in direct mode",
                    server_ip=server_ips_str, domain_ip=dips_str))
                
        if domain_ip_matches_server and model.mode in [DomainType.cdn, DomainType.relay, DomainType.fake, DomainType.auto_cdn_ip]:
            raise ValidationError(
                __("In CDN mode, Domain IP=%(domain_ip)s should be different to your ip=%(server_ip)s",
                    server_ip=server_ips_str, domain_ip=dips_str))
                
        return True
    
        
    # def after_model_change(self,form, model, is_created):
    #     if model.show_domains.count==0:
    #         db.session.bulk_save_objects(ShowDomain(model.id,model.id))

    def on_model_delete(self, model):
        if len(Domain.query.all()) <= 1:
            raise ValidationError(f"at least one domain should exist")
        if hconfig(ConfigEnum.cloudflare) and model.mode not in [DomainType.fake, DomainType.reality, DomainType.relay] and "special" not in model.mode:
            if not hutils.network.cf_api.delete_dns_record(model.domain):
                hutils.flask.flash(_('cf-delete.failed'), 'warning')  # type: ignore
        model.showed_by_domains = []
        # db.session.commit()
        hutils.flask.flash_config_success(restart_mode=ApplyMode.apply_config, domain_changed=True)

    def after_model_delete(self, model):
        if hutils.node.is_child():
            hutils.node.run_node_op_in_bg(hutils.node.child.sync_with_parent, *[hutils.node.child.SyncFields.domains])

    def after_model_change(self, form, model, is_created):
        if hconfig(ConfigEnum.first_setup):
            set_hconfig(ConfigEnum.first_setup, False)
        if model.need_valid_ssl and "*" not in model.domain:
            commander(Command.get_cert, domain=model.domain)
        if hutils.node.is_child():
            hutils.node.run_node_op_in_bg(hutils.node.child.sync_with_parent, *[hutils.node.child.SyncFields.domains])

    def is_accessible(self):
        if login_required(roles={Role.super_admin, Role.admin})(lambda: True)() != True:
            return False
        return True

    # def form_choices(self, field, *args, **kwargs):
    #     if field.type == "Enum":
    #         return [(enum_value.name, _(enum_value.name)) for enum_value in field.type.__members__.values()]
    #     return super().form_choices(field, *args, **kwargs)

    # @property
    # def server_ips(self):
    #     return hiddify.get_ip(4)

    def get_query(self):
        query = super().get_query()
        return query.filter(Domain.child_id == Child.current().id)
