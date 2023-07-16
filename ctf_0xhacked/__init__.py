import os
import json
import subprocess
from flask import Blueprint, request
from CTFd.models import (
    ChallengeFiles,
    Challenges,
    Fails,
    Flags,
    Hints,
    Solves,
    Tags,
    db,
)
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.flags import FlagException, get_flag_class, FLAG_CLASSES
from CTFd.plugins.challenges import BaseChallenge, CHALLENGE_CLASSES
from CTFd.plugins.dynamic_challenges import DECAY_FUNCTIONS, logarithmic
from CTFd.schemas.files import FileSchema
from CTFd.utils import uploads
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_ip

ZK_VERIFY_BIN = ""

blueprint = Blueprint(
    "0xhacked", __name__, template_folder="templates", static_folder="assets"
)

@blueprint.route('/proof', methods=['POST'])
@authed_only
def upload_proof():
    if 'file' not in request.files:
        return {"success": False, "errors": "No file part"}, 400
    file = request.files['file']
    if file.filename == '':
        return {"success": False, "errors": "No selected file"}, 400
    obj = uploads.upload_file(file=file, type='proof')
    schema = FileSchema()
    response = schema.dump(obj)
    if response.errors:
        return {"success": False, "errors": response.errorss}, 400

    return {"success": True, "data": response.data}


class DynamicZkpChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "dynamic_zkp"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)
    function = db.Column(db.String(32), default="logarithmic")

    def __init__(self, *args, **kwargs):
        super(DynamicZkpChallenge, self).__init__(**kwargs)
        self.value = kwargs["initial"]


class ZKPChallenge(BaseChallenge):
    id = "dynamic_zkp"  # Unique identifier used to register challenges
    name = "dynamic_zkp"  # Name of a challenge type
    templates = {  # Templates used for each aspect of challenge editing & viewing
        "create": "/plugins/ctf_0xhacked/assets/create.html",
        "update": "/plugins/ctf_0xhacked/assets/update.html",
        "view": "/plugins/ctf_0xhacked/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/ctf_0xhacked/assets/create.js",
        "update": "/plugins/ctf_0xhacked/assets/update.js",
        "view": "/plugins/ctf_0xhacked/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/ctf_0xhacked/assets/"
    
    challenge_model = DynamicZkpChallenge

    @classmethod
    def calculate_value(cls, challenge):
        f = DECAY_FUNCTIONS.get(challenge.function, logarithmic)
        value = f(challenge)

        challenge.value = value
        db.session.commit()
        return challenge

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = DynamicZkpChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "connection_info": challenge.connection_info,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()

        for attr, value in data.items():
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        return cls.calculate_value(challenge)

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        cls.calculate_value(challenge)


def verify_file(verify_bin: str, proof: str, rpc_url: str):
    args = [
        verify_bin,
        "-r",
        rpc_url,
        str(proof)
    ]
    
    proc = subprocess.run(
        args,
        capture_output=True
    )
    if proc.returncode != 0:
        return False, proc.stderr.decode()
    return True, json.loads(proc.stdout)


class ZKPFlag:
    name = "zkp"
    templates = {
        "create": "/plugins/ctf_0xhacked/assets/flag/create.html",
        "update": "/plugins/ctf_0xhacked/assets/flag/edit.html"
    }

    @staticmethod
    def compare(chal_key_obj, provided):
        data = json.loads(chal_key_obj.data)
        uploader = uploads.get_uploader()
        proof_path = os.path.join(uploader.base_path, provided)
        try:
            flag, proof = verify_file(ZK_VERIFY_BIN, proof_path, data['eth_rpc_url'])
            if not flag:
                return False
        except Exception as e:
            print(e)
            return False

        if proof['block_number'] != int(data['block_number']):
            return False

        code = compile(chal_key_obj.content, '<string>', 'exec')
        scope = {}
        exec(code, scope)

        return scope['check'](data, proof)



def load(app):
    FLAG_CLASSES[ZKPFlag.name] = ZKPFlag
    CHALLENGE_CLASSES[ZKPChallenge.name] = ZKPChallenge
    register_plugin_assets_directory(app, base_path="/plugins/ctf_0xhacked/assets/")
    app.register_blueprint(blueprint)
