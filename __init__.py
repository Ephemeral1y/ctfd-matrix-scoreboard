import os

from flask import (
    render_template,
    jsonify,
    Blueprint,
    url_for,
    session,
    redirect,
    request
)
from sqlalchemy.sql import or_

from CTFd import utils, scoreboard
from CTFd.models import db, Solves, Challenges
from CTFd.plugins import override_template
from CTFd.utils.config import is_scoreboard_frozen, ctf_theme, is_users_mode
from CTFd.utils.config.visibility import challenges_visible, scores_visible
from CTFd.utils.dates import (
    ctf_started, ctftime, view_after_ctf, unix_time_to_utc
)
from CTFd.utils.user import is_admin, authed

NumberOfChallenges = 40 # 题目数量
num_re = 0
num_cry = 0
num_pwn = 0
num_web = 0
num_misc = 0

def load(app):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(dir_path, 'scoreboard-matrix.html')
    override_template('scoreboard.html', open(template_path).read())

    matrix = Blueprint('matrix', __name__, static_folder='static')
    app.register_blueprint(matrix, url_prefix='/matrix')

    def get_standings():
        standings = scoreboard.get_standings()
        # TODO faster lookup here
        jstandings = []
        for team in standings:
            teamid = team[0]
            solves = db.session.query(Solves.challenge_id.label('challenge_id'), Solves.date.label('date')).filter(Solves.user_id == teamid)
            freeze = utils.get_config('freeze')
            if freeze:
                freeze = unix_time_to_utc(freeze)
                if teamid != session.get('id'):
                    solves = solves.filter(Solves.date < freeze)
            solves = solves.all()
            jsolves = []
            blood = [[] for i in range(NumberOfChallenges)]   
            score = 0
            for solve in solves:
                cvalue = Challenges.query.filter_by(id=solve.challenge_id).first().value
                top = Solves.query.filter_by(challenge_id=solve.challenge_id, type='correct').order_by(Solves.date.asc()).all()
                slovenum = ''
                if(solve.date == top[0].date):
                    solvenum = solve.challenge_id
                    score = score + int(cvalue * 1.1)   #一血加成10%
                    blood[solve.challenge_id].append(1)
                elif(solve.date == top[1].date):
                    solvenum = solve.challenge_id
                    score = score + int(cvalue * 1.05)  #二血加成5%
                    blood[solve.challenge_id].append(2)
                elif(solve.date == top[2].date):
                    solvenum = solve.challenge_id
                    score = score + int(cvalue * 1.03)  #三血加成3%
                    blood[solve.challenge_id].append(3)
                else:
                    solvenum = solve.challenge_id
                    score = score + int(cvalue * 1)
                    blood[solve.challenge_id].append(0)
                jsolves.append(solvenum)
            jstandings.append({'teamid': team[0], 'score': int(score), 'name': team[2], 'solves': jsolves, 'blood': blood})
        jstandings.sort(key=lambda x: x["score"], reverse=True)
        db.session.close()
        return jstandings

    def get_challenges():
        global num_re
        global num_cry
        global num_pwn 
        global num_web
        global num_misc
        num_re = 0
        num_cry = 0
        num_pwn = 0 
        num_web = 0
        num_misc = 0
        if not is_admin():
            if not ctftime():
                if view_after_ctf():
                    pass
                else:
                    return []
        if challenges_visible() and (ctf_started() or is_admin()):
            chals = db.session.query(
                Challenges.id,
                Challenges.name,
                Challenges.category,
                Challenges.value
            ).filter(or_(Challenges.state != 'hidden', Challenges.state is None)).order_by(Challenges.category.asc()).all()
            jchals = []

            
            for x in chals:
                if "REVERSE" in x.category:
                    num_re += 1
                elif "CRYPTO" in x.category:
                    num_cry += 1
                elif "PWN" in x.category:
                    num_pwn += 1
                elif "WEB" in x.category:
                    num_web += 1
                elif "MISC" in x.category:
                    num_misc += 1
                else:
                    pass
            
            for x in chals:
                    jchals.append({
                    'id': x.id,
                    'name': x.name,
                    'category': x.category,
                    'value' : x.value,
                })  

            # Sort into groups
            # categories = set(map(lambda x: x['category'], jchals))
            # jchals = [j for c in categories for j in jchals if j['category'] == c]
            return jchals
        return []
    
    def set_re(re):
        num_re = re
        return ""

    def set_pwn(pwn):
        num_pwn = pwn
        return ""

    def set_misc(misc):
        num_misc = misc
        return ""

    def set_cry(cry):
        num_cry = cry
        return ""

    def set_web(web):
        num_web = web
        return ""
            
    def get_re():
        return num_re

    def get_cry():
        return num_cry

    def get_pwn():
        return num_pwn

    def get_web():
        return num_web

    def get_misc():
        return num_misc


    def scoreboard_view():
        if scores_visible() and not authed():
            return redirect(url_for('auth.login', next=request.path))
        if not scores_visible():
            return render_template('scoreboard.html',
                                   errors=['Scores are currently hidden'])
        standings = get_standings()
        return render_template('scoreboard.html', standings=standings,
                               score_frozen=is_scoreboard_frozen(),
                               mode='users' if is_users_mode() else 'teams',
                               challenges=get_challenges(), theme=ctf_theme())

    def scores():
        json = {'standings': []}
        if scores_visible() and not authed():
            return redirect(url_for('auth.login', next=request.path))
        if not scores_visible():
            return jsonify(json)

        standings = get_standings()

        for i, x in enumerate(standings):
            json['standings'].append({'pos': i + 1, 'id': x['name'], 'team': x['name'],
                                      'score': int(x['score']), 'solves': x['solves']})
        return jsonify(json)

    app.view_functions['scoreboard.listing'] = scoreboard_view
    app.view_functions['scoreboard.score'] = scores
    app.add_template_global(get_re, 'get_re')
    app.add_template_global(get_pwn, 'get_pwn')
    app.add_template_global(get_misc, 'get_misc')
    app.add_template_global(get_cry, 'get_cry')
    app.add_template_global(get_web, 'get_web')
    app.add_template_global(set_re, 'set_re')
    app.add_template_global(set_pwn, 'set_pwn')
    app.add_template_global(set_misc, 'set_misc')
    app.add_template_global(set_cry, 'set_cry')
    app.add_template_global(set_web, 'set_web')
