# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`
import os

from firebase_functions import https_fn, options
from firebase_admin import initialize_app
from solver.solve_game import execute
from flask import json

initialize_app()


@https_fn.on_request()
def solve(req: https_fn.Request):
    game_text = req.form.get('game_text')
    file = open(os.path.join(os.getcwd(),"solver/input/game_to_solve.txt"), "w+")
    file.write(str(game_text))
    file.close()
    result = execute()
    headers = {
        'Access-Control-Allow-Origin': '*',
    }
    return (json.dumps(result), 200, headers)
