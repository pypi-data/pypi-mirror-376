"""
Utility functions for Nginx configuration management.

This module provides helper functions for managing Nginx configurations,
including YAML parsing, configuration deployment, and input validation.
All functions are designed to work with the nginx_set_conf package.

Typical usage example:
    yaml_config = parse_yaml('config.yaml')
    execute_commands(yaml_config['template'], yaml_config['domain'], ...)
"""

# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import yaml
from .config_templates import get_config_template


def fire_all_functions(function_list: list) -> None:
    """Executes a list of functions in sequence.

    Args:
        function_list: A list of callable functions to be executed.
    """
    for func in function_list:
        func()


def self_clean(input_dictionary: dict) -> dict:
    """Removes duplicate values from dictionary values while preserving keys.

    Args:
        input_dictionary: Dictionary to clean.

    Returns:
        A new dictionary with duplicate values removed from each key's value list.
    """
    return_dict = input_dictionary.copy()
    for key, value in input_dictionary.items():
        return_dict[key] = list(dict.fromkeys(value))
    return return_dict


def parse_yaml(yaml_file: str) -> dict:
    """Parses a YAML file into a Python dictionary.

    Args:
        yaml_file: Path to the YAML file to parse.

    Returns:
        Dictionary containing the parsed YAML data.
        Returns False if parsing fails.

    Raises:
        yaml.YAMLError: If the YAML file is malformed.
    """
    with open(yaml_file, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return False


def parse_yaml_folder(path: str) -> list:
    """Parses all YAML files in a directory.

    Searches for files with .yaml or .yml extensions in the specified directory
    and parses each one into a Python object.

    Args:
        path: Directory path containing YAML files.

    Returns:
        List of parsed YAML objects.
    """
    yaml_objects = []
    for file in os.listdir(path):
        if file.endswith(".yaml") or file.endswith(".yml"):
            yaml_object = parse_yaml(os.path.join(path, file))
            if yaml_object:
                yaml_objects.append(yaml_object)
    return yaml_objects


def get_default_vars() -> dict:
    """Returns default variables for Nginx configuration.

    Returns:
        Dictionary containing default values for Nginx configuration variables
        including server paths, domains, ports, and certificate locations.
    """
    return {
        "server_path": "/etc/nginx/conf.d",
        "template_domain": "server.domain.de",
        "template_ip": "ip.ip.ip.ip",
        "template_port": "{{PORT}}",
        "template_poll_port": "{{POLL_PORT}}",
        "template_grpc_port": "{{GRPC_PORT}}",
        "template_crt": "zertifikat.crt",
        "template_key": "zertifikat.key",
        "template_self_crt": "/etc/letsencrypt/live/zertifikat.crt/fullchain.pem",
        "template_self_key": "/etc/letsencrypt/live/zertifikat.key/privkey.pem",
        "template_redirect_domain": "target.domain.de",
        "template_auth_file": "authfile",
    }


def retrieve_valid_input(message: str) -> str:
    """Prompts user for input until non-empty input is provided.

    Args:
        message: Prompt message to display to user.

    Returns:
        User's non-empty input string.
    """
    user_input = input(message)
    if user_input:
        return user_input
    else:
        return retrieve_valid_input(message)


def execute_commands(
    config_template, domain, ip, cert_name, cert_key, port, pollport, redirect_domain, auth_file, allowed_ips,
    target_path=None, dry_run=False, grpcport=None, disable_domain_listen=False
):
    """Generates and deploys Nginx config files based on input parameters.

    Args:
        config_template: Template name for Nginx configuration.
        domain: Domain name for Nginx configuration.
        ip: IP address for Nginx configuration.
        cert_name: Certificate name for Nginx configuration.
        cert_key: Certificate key for Nginx configuration.
        port: Port number for Nginx configuration.
        pollport: Polling port number for Nginx configuration (optional).
        redirect_domain: Redirect domain for Nginx configuration (optional).
        auth_file: Authentication file for Nginx configuration (optional).
        allowed_ips: Comma-separated list of allowed IPs/CIDR blocks (optional).
        target_path: Custom target path for generated configs (optional, default is /etc/nginx/conf.d).
        dry_run: If True, display commands without executing them (optional, default is False).
        grpcport: gRPC port number for Nginx configuration (optional, used by Qdrant template).
    """
    # Get default vars
    default_vars = get_default_vars()
    server_path = target_path if target_path else default_vars["server_path"]
    template_domain = default_vars["template_domain"]
    template_ip = default_vars["template_ip"]
    template_crt = default_vars["template_crt"]
    template_key = default_vars["template_key"]
    template_self_crt = default_vars["template_self_crt"]
    template_self_key = default_vars["template_self_key"]
    template_port = default_vars["template_port"]
    template_poll_port = default_vars["template_poll_port"]
    template_grpc_port = default_vars["template_grpc_port"]
    template_redirect_domain = default_vars["template_redirect_domain"]
    
    # Create target directory if it doesn't exist
    if not dry_run and target_path and not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
        print(f"Created directory: {target_path}")
    
    # Extract service name from template name
    service_name = config_template.replace('ngx_', '')
    
    # Create unique cache directory if needed
    # Use domain in the cache path to ensure uniqueness
    if domain:
        domain_id = domain.replace('.', '_')
        unique_id = f"{service_name}_{domain_id}"
    else:
        unique_id = service_name
    
    cache_dir = f"/var/cache/nginx/{unique_id}"
    print(f"Using domain-specific cache path: {cache_dir}")
    
    if not dry_run and not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir, exist_ok=True)
            print(f"Created cache directory: {cache_dir}")
            # Set proper permissions for nginx
            os.system(f"chown -R nginx:nginx {cache_dir}")
            os.system(f"chmod -R 755 {cache_dir}")
            print(f"Set permissions for: {cache_dir}")
        except Exception as e:
            print(f"Warning: Could not create cache directory: {e}")
    elif dry_run:
        print(f"[DRY RUN] Would create cache directory: {cache_dir}")
    
    # Get config templates with domain-specific cache paths
    print(f"Generating domain-specific template for {domain} using {config_template}")
    config_template_content = get_config_template(config_template, domain)
    
    # Debug info: Print the proxy_cache_path line from the template
    for line in config_template_content.split('\n'):
        if 'proxy_cache_path' in line:
            print(f"DEBUG - Cache path in template: {line}")
    
    if config_template_content:
        current_path = os.path.dirname(os.path.realpath(__file__))
        file_path = current_path + "/" + config_template + ".conf"
        with open(file_path, "w") as f:
            f.write(config_template_content)
            
        # Debug info: Verify cache path in written file
        with open(file_path, "r") as f:
            for line in f:
                if 'proxy_cache_path' in line:
                    print(f"DEBUG - Cache path in written file: {line.strip()}")
        
        # DIRECT FIX: Ensure the cache path is correctly set in the file
        # This is a very direct approach to ensure the path is correct
        import re
        with open(file_path, "r") as f:
            content = f.read()
        
        # Create a more robust replacement for cache paths
        domain_safe = domain.replace('.', '_')
        unique_id = f"{service_name}_{domain_safe}"
        
        # Directly replace any proxy_cache_path that matches the pattern, regardless of content
        content = re.sub(
            r'proxy_cache_path\s+/var/cache/nginx/[^\s]+', 
            f'proxy_cache_path /var/cache/nginx/{unique_id}',
            content
        )
        
        # Specifically fix the keys_zone= parameter in proxy_cache_path lines only
        content = re.sub(
            r'(proxy_cache_path\s+[^\s]+\s+[^;]*keys_zone=)[^\s:]+:', 
            f'\\1{unique_id}_cache:',
            content
        )
        
        # Specifically fix the zone= parameter in limit_req_zone lines only
        content = re.sub(
            r'(limit_req_zone\s+[^\s]+\s+zone=)[^\s:]+:', 
            f'\\1{unique_id}_ratelimit:',
            content
        )
        
        # Fix any limit_req directives referencing the zone
        content = re.sub(
            r'(limit_req\s+zone=)[^\s;]+', 
            f'\\1{unique_id}_ratelimit',
            content
        )
        
        # Write the updated content back
        with open(file_path, "w") as f:
            f.write(content)
            print("Direct cache path fix applied to configuration")
            
        # Verify the fix
        with open(file_path, "r") as f:
            for line in f:
                if 'proxy_cache_path' in line or 'keys_zone=' in line or 'zone=' in line:
                    print(f"FIXED - Line: {line.strip()}")
        
        # copy command
        eq_display_message = (
            "Copy " + file_path + " " + server_path + "/" + domain + ".conf"
        )
        eq_copy_command = "cp " + file_path + " " + server_path + "/" + domain + ".conf"
        print(eq_display_message.rstrip("\n"))
        if not dry_run:
            os.system(eq_copy_command)
            print(eq_copy_command.rstrip("\n"))
            os.remove(file_path)
            
            # VERIFY final configuration
            final_config_path = server_path + "/" + domain + ".conf"
            if os.path.exists(final_config_path):
                print(f"Verifying cache path in the final config: {final_config_path}")
                with open(final_config_path, "r") as f:
                    for line in f:
                        if 'proxy_cache_path' in line:
                            print(f"FINAL CONFIG - Cache path: {line.strip()}")
        else:
            print(f"[DRY RUN] Would execute: {eq_copy_command}")
    else:
        print("No valid config template")
        return

    # send command - domain
    eq_display_message = "Set domain name in conf to " + domain
    eq_set_domain_cmd = (
        "sed -i 's|"
        + template_domain
        + "|"
        + domain
        + "|g' "
        + server_path
        + "/"
        + domain
        + ".conf"
    )
    print(eq_display_message.rstrip("\n"))
    if not dry_run:
        os.system(eq_set_domain_cmd)
        print(eq_set_domain_cmd.rstrip("\n"))
    else:
        print(f"[DRY RUN] Would execute: {eq_set_domain_cmd}")

    # Handle disable_domain_listen parameter - remove domain from listen directives
    if disable_domain_listen:
        eq_display_message = "Removing domain prefix from listen directives (for intranet systems)"
        print(eq_display_message.rstrip("\n"))
        
        # Remove domain prefix from HTTP listen directive (e.g., "listen domain.com:80" -> "listen 80")
        eq_remove_domain_http_cmd = (
            "sed -i 's|listen " + domain + ":80|listen 80|g' " 
            + server_path + "/" + domain + ".conf"
        )
        
        # Remove domain prefix from HTTPS listen directive (e.g., "listen domain.com:443" -> "listen 443")
        eq_remove_domain_https_cmd = (
            "sed -i 's|listen " + domain + ":443|listen 443|g' " 
            + server_path + "/" + domain + ".conf"
        )
        
        if not dry_run:
            os.system(eq_remove_domain_http_cmd)
            print(eq_remove_domain_http_cmd.rstrip("\n"))
            os.system(eq_remove_domain_https_cmd)
            print(eq_remove_domain_https_cmd.rstrip("\n"))
        else:
            print(f"[DRY RUN] Would execute: {eq_remove_domain_http_cmd}")
            print(f"[DRY RUN] Would execute: {eq_remove_domain_https_cmd}")

    # send command - ip
    eq_display_message = "Set ip in conf to " + ip
    eq_set_ip_cmd = (
        "sed -i 's|" + template_ip + "|" + ip + "|g' " + server_path + "/" + domain + ".conf"
    )
    print(eq_display_message.rstrip("\n"))
    if not dry_run:
        os.system(eq_set_ip_cmd)
        print(eq_set_ip_cmd.rstrip("\n"))
    else:
        print(f"[DRY RUN] Would execute: {eq_set_ip_cmd}")

    if cert_key != "":
        template_crt = template_self_crt
        template_key = template_self_key
    else:
        cert_key = cert_name

    # send command - cert, key
    eq_display_message = "Set cert name in conf to " + cert_name
    eq_set_cert_cmd = (
        "sed -i 's|"
        + template_crt
        + "|"
        + cert_name
        + "|g' "
        + server_path
        + "/"
        + domain
        + ".conf"
    )
    eq_set_key_cmd = (
        "sed -i 's|"
        + template_key
        + "|"
        + cert_key
        + "|g' "
        + server_path
        + "/"
        + domain
        + ".conf"
    )
    print(eq_display_message.rstrip("\n"))
    if not dry_run:
        os.system(eq_set_cert_cmd)
        print(eq_set_cert_cmd.rstrip("\n"))
        os.system(eq_set_key_cmd)
        print(eq_set_key_cmd.rstrip("\n"))
    else:
        print(f"[DRY RUN] Would execute: {eq_set_cert_cmd}")
        print(f"[DRY RUN] Would execute: {eq_set_key_cmd}")

    # Letsencrypt - skip certificate creation during dry run
    if cert_key == cert_name and not dry_run:
        # Search for certificate and create it when it does not exist
        cert_exists = os.path.isfile(
            "/etc/letsencrypt/live/" + cert_name + "/fullchain.pem"
        ) and os.path.isfile("/etc/letsencrypt/live/" + cert_name + "/privkey.pem")
        if not cert_exists:
            os.system("systemctl stop nginx.service")
            eq_create_cert = (
                "certbot certonly --standalone --agree-tos --register-unsafely-without-email -d "
                + cert_name
            )
            os.system(eq_create_cert)
            print(eq_create_cert.rstrip("\n"))
    elif cert_key == cert_name and dry_run:
        print(f"[DRY RUN] Would check for and possibly create certificate for: {cert_name}")

    # send command - port
    if port:
        eq_display_message = "Set port in conf to " + port
        eq_set_port_cmd = (
            "sed -i 's|"
            + template_port
            + "|"
            + port
            + "|g' "
            + server_path
            + "/"
            + domain
            + ".conf"
        )
        print(eq_display_message.rstrip("\n"))
        if not dry_run:
            os.system(eq_set_port_cmd)
            print(eq_set_port_cmd.rstrip("\n"))
        else:
            print(f"[DRY RUN] Would execute: {eq_set_port_cmd}")

    # send command - poll port
    if pollport:
        eq_display_message = "Set poll port in conf to " + pollport
        eq_set_poll_port_cmd = (
            "sed -i 's|"
            + template_poll_port
            + "|"
            + pollport
            + "|g' "
            + server_path
            + "/"
            + domain
            + ".conf"
        )
        print(eq_display_message.rstrip("\n"))
        if not dry_run:
            os.system(eq_set_poll_port_cmd)
            print(eq_set_poll_port_cmd.rstrip("\n"))
        else:
            print(f"[DRY RUN] Would execute: {eq_set_poll_port_cmd}")
            
    # send command - grpc port
    if grpcport:
        eq_display_message = "Set gRPC port in conf to " + grpcport
        eq_set_grpc_port_cmd = (
            "sed -i 's|"
            + template_grpc_port
            + "|"
            + grpcport
            + "|g' "
            + server_path
            + "/"
            + domain
            + ".conf"
        )
        print(eq_display_message.rstrip("\n"))
        if not dry_run:
            os.system(eq_set_grpc_port_cmd)
            print(eq_set_grpc_port_cmd.rstrip("\n"))
        else:
            print(f"[DRY RUN] Would execute: {eq_set_grpc_port_cmd}")

    # authentication
    eq_display_message = "Try set auth file to " + auth_file
    print(eq_display_message.rstrip("\n"))
    if auth_file:
        eq_display_message = "Set auth file to " + auth_file
        print(eq_display_message.rstrip("\n"))
        _filename = server_path + "/" + domain + ".conf"
        
        if not dry_run:
            with open(_filename, "r", encoding="utf-8") as _file:
                _data = _file.readlines()
        
            # Find the index of the line containing #authentication and add 1 to insert after this line
            insertion_index = None
            for i, line in enumerate(_data):
                if '#authentication' in line:  # Check if this is the line we're looking for
                    insertion_index = i + 1
                    break
        
            # If the marker was found, insert the authentication lines after it
            if insertion_index is not None:
                _data.insert(insertion_index, '        auth_basic       "Restricted Area";' + "\n")
                _data.insert(insertion_index + 1, "        auth_basic_user_file  " + auth_file + ";" + "\n")
        
            with open(_filename, "w", encoding="utf-8") as _file:
                _file.writelines(_data)
        else:
            print(f"[DRY RUN] Would add authentication settings using: {auth_file}")

    # IP restrictions processing - only if allowed_ips parameter is provided
    if allowed_ips:
        eq_display_message = f"Set IP restrictions to {allowed_ips}"
        print(eq_display_message.rstrip("\n"))
        _filename = server_path + "/" + domain + ".conf"
        
        if not dry_run:
            with open(_filename, "r", encoding="utf-8") as _file:
                _data = _file.readlines()
        
            # Find the index of the line containing #ip_restrictions and add 1 to insert after this line
            insertion_index = None
            for i, line in enumerate(_data):
                if '#ip_restrictions' in line:  # Check if this is the line we're looking for
                    insertion_index = i + 1
                    break
        
            # If the marker was found, insert the IP restriction lines after it
            if insertion_index is not None:
                # Add comment and IP restrictions
                _data.insert(insertion_index, '    # IP restrictions\n')
                insertion_index += 1
                
                # Parse and insert each IP/CIDR block
                for ip_entry in allowed_ips.split(','):
                    ip_entry = ip_entry.strip()
                    if ip_entry:  # Only add non-empty entries
                        _data.insert(insertion_index, f'    allow {ip_entry};\n')
                        insertion_index += 1
                
                # Add deny all at the end
                _data.insert(insertion_index, '    deny all;\n')
        
            with open(_filename, "w", encoding="utf-8") as _file:
                _file.writelines(_data)
        else:
            print(f"[DRY RUN] Would add IP restrictions: {allowed_ips}")

    if "redirect" in config_template and redirect_domain:
        # send command - redirect domain
        eq_display_message = "Set redirect domain in conf to " + redirect_domain
        eq_set_redirect_cmd = (
            "sed -i 's|"
            + template_redirect_domain
            + "|"
            + redirect_domain
            + "|g' "
            + server_path
            + "/"
            + domain
            + ".conf"
        )
        print(eq_display_message.rstrip("\n"))
        if not dry_run:
            os.system(eq_set_redirect_cmd)
            print(eq_set_redirect_cmd.rstrip("\n"))
        else:
            print(f"[DRY RUN] Would execute: {eq_set_redirect_cmd}")

    # Search for certificate and create it when it does not exist
    if "redirect_ssl" in config_template and redirect_domain and not dry_run:
        cert_exists = os.path.isfile(
            "/etc/letsencrypt/live/" + redirect_domain + "/fullchain.pem"
        ) and os.path.isfile(
            "/etc/letsencrypt/live/" + redirect_domain + "/privkey.pem"
        )
        if not cert_exists:
            os.system("systemctl stop nginx.service")
            eq_create_cert = (
                "certbot certonly --standalone --agree-tos --register-unsafely-without-email -d "
                + redirect_domain
            )
            os.system(eq_create_cert)
            print(eq_create_cert.rstrip("\n"))
    elif "redirect_ssl" in config_template and redirect_domain and dry_run:
        print(f"[DRY RUN] Would check for and possibly create certificate for redirect domain: {redirect_domain}")
