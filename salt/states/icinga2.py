"""
Icinga2 state
=============

.. versionadded:: 2017.7.0

:depends:   - Icinga2 Python module
:configuration: See :py:mod:`salt.modules.icinga2` for setup instructions.

The icinga2 module is used to execute commands.
Its output may be stored in a file or in a grain.

.. code-block:: yaml

    command_id:
      icinga2.generate_ticket:
        - name: domain.tld
        - output:  "/tmp/query_id.txt"
"""


import os.path

import salt.utils.files
import salt.utils.stringutils
from salt.utils.icinga2 import get_certs_path


def __virtual__():
    """
    Only load if the icinga2 module is available in __salt__
    """
    if "icinga2.generate_ticket" in __salt__:
        return True
    return (False, "icinga2 module could not be loaded")


def generate_ticket(name, output=None, grain=None, key=None, overwrite=True):
    """
    Generate an icinga2 ticket on the master.

    name
        The domain name for which this ticket will be generated

    output
        grain: output in a grain
        other: the file to store results
        None:  output to the result comment (default)

    grain:
        grain to store the output (need output=grain)

    key:
        the specified grain will be treated as a dictionary, the result
        of this state will be stored under the specified key.

    overwrite:
        The file or grain will be overwritten if it already exists (default)
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    # Checking if execution is needed.
    if output == "grain":
        if grain and not key:
            if not overwrite and grain in __salt__["grains.ls"]():
                ret["comment"] = "No execution needed. Grain {} already set".format(
                    grain
                )
                return ret
            elif __opts__["test"]:
                ret["result"] = None
                ret[
                    "comment"
                ] = "Ticket generation would be executed, storing result in grain: {}".format(
                    grain
                )
                return ret
        elif grain:
            if grain in __salt__["grains.ls"]():
                grain_value = __salt__["grains.get"](grain)
            else:
                grain_value = {}
            if not overwrite and key in grain_value:
                ret["comment"] = "No execution needed. Grain {}:{} already set".format(
                    grain, key
                )
                return ret
            elif __opts__["test"]:
                ret["result"] = None
                ret[
                    "comment"
                ] = "Ticket generation would be executed, storing result in grain: {}:{}".format(
                    grain, key
                )
                return ret
        else:
            ret["result"] = False
            ret["comment"] = "Error: output type 'grain' needs the grain parameter\n"
            return ret
    elif output:
        if not overwrite and os.path.isfile(output):
            ret["comment"] = "No execution needed. File {} already set".format(output)
            return ret
        elif __opts__["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "Ticket generation would be executed, storing result in file: {}".format(
                output
            )
            return ret
    elif __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "Ticket generation would be executed, not storing result"
        return ret

    # Executing the command.
    ticket_res = __salt__["icinga2.generate_ticket"](name)
    ticket = ticket_res["stdout"]
    if not ticket_res["retcode"]:
        ret["comment"] = str(ticket)

    if output == "grain":
        if grain and not key:
            __salt__["grains.setval"](grain, ticket)
            ret["changes"]["ticket"] = "Executed. Output into grain: {}".format(grain)
        elif grain:
            if grain in __salt__["grains.ls"]():
                grain_value = __salt__["grains.get"](grain)
            else:
                grain_value = {}
            grain_value[key] = ticket
            __salt__["grains.setval"](grain, grain_value)
            ret["changes"]["ticket"] = "Executed. Output into grain: {}:{}".format(
                grain, key
            )
    elif output:
        ret["changes"]["ticket"] = "Executed. Output into {}".format(output)
        with salt.utils.files.fopen(output, "w") as output_file:
            output_file.write(salt.utils.stringutils.to_str(ticket))
    else:
        ret["changes"]["ticket"] = "Executed"

    return ret


def generate_cert(name):
    """
    Generate an icinga2 certificate and key on the client.

    name
        The domain name for which this certificate and key will be generated
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    cert = "{}{}.crt".format(get_certs_path(), name)
    key = "{}{}.key".format(get_certs_path(), name)

    # Checking if execution is needed.
    if os.path.isfile(cert) and os.path.isfile(key):
        ret[
            "comment"
        ] = "No execution needed. Cert: {} and key: {} already generated.".format(
            cert, key
        )
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "Certificate and key generation would be executed"
        return ret

    # Executing the command.
    cert_save = __salt__["icinga2.generate_cert"](name)
    if not cert_save["retcode"]:
        ret["comment"] = "Certificate and key generated"
        ret["changes"]["cert"] = "Executed. Certificate saved: {}".format(cert)
        ret["changes"]["key"] = "Executed. Key saved: {}".format(key)
    return ret


def save_cert(name, master):
    """
    Save the certificate on master icinga2 node.

    name
        The domain name for which this certificate will be saved

    master
        Icinga2 master node for which this certificate will be saved
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    cert = "{}trusted-master.crt".format(get_certs_path())

    # Checking if execution is needed.
    if os.path.isfile(cert):
        ret["comment"] = "No execution needed. Cert: {} already saved.".format(cert)
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "Certificate save for icinga2 master would be executed"
        return ret

    # Executing the command.
    cert_save = __salt__["icinga2.save_cert"](name, master)
    if not cert_save["retcode"]:
        ret["comment"] = "Certificate for icinga2 master saved"
        ret["changes"]["cert"] = "Executed. Certificate saved: {}".format(cert)
    return ret


def request_cert(name, master, ticket, port="5665"):
    """
    Request CA certificate from master icinga2 node.

    name
        The domain name for which this certificate will be saved

    master
        Icinga2 master node for which this certificate will be saved

    ticket
        Authentication ticket generated on icinga2 master

    port
        Icinga2 port, defaults to 5665
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    cert = "{}ca.crt".format(get_certs_path())

    # Checking if execution is needed.
    if os.path.isfile(cert):
        ret["comment"] = "No execution needed. Cert: {} already exists.".format(cert)
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "Certificate request from icinga2 master would be executed"
        return ret

    # Executing the command.
    cert_request = __salt__["icinga2.request_cert"](name, master, ticket, port)
    if not cert_request["retcode"]:
        ret["comment"] = "Certificate request from icinga2 master executed"
        ret["changes"]["cert"] = "Executed. Certificate requested: {}".format(cert)
        return ret

    ret["comment"] = "FAILED. Certificate requested failed with output: {}".format(
        cert_request["stdout"]
    )
    ret["result"] = False
    return ret


def node_setup(name, master, ticket):
    """
    Setup the icinga2 node.

    name
        The domain name for which this certificate will be saved

    master
        Icinga2 master node for which this certificate will be saved

    ticket
        Authentication ticket generated on icinga2 master
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    cert = "{}{}.crt.orig".format(get_certs_path(), name)
    key = "{}{}.key.orig".format(get_certs_path(), name)

    # Checking if execution is needed.
    if os.path.isfile(cert) and os.path.isfile(cert):
        ret["comment"] = "No execution needed. Node already configured."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "Node setup will be executed."
        return ret

    # Executing the command.
    node_setup = __salt__["icinga2.node_setup"](name, master, ticket)
    if not node_setup["retcode"]:
        ret["comment"] = "Node setup executed."
        ret["changes"]["cert"] = "Node setup finished successfully."
        return ret

    ret["comment"] = "FAILED. Node setup failed with outpu: {}".format(
        node_setup["stdout"]
    )
    ret["result"] = False
    return ret
