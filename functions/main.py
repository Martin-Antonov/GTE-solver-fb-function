# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`
import os

from firebase_functions import https_fn
from firebase_admin import initialize_app
from solver.solve_game import execute

initialize_app()


@https_fn.on_request()
def solve(req: https_fn.Request) -> https_fn.Response:
    game_text = req.form.get('game_text')
    file = open(os.path.join(os.getcwd(),"solver/input/game_to_solve.txt"), "w+")
    file.write(str(game_text))
    file.close()
    result = execute()
    return result
