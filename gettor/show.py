from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import webbrowser
from werkzeug.exceptions import abort

from gettor.auth import login_required
from gettor import db
from gettor.models.models import Show, ShowToTvmaze
from gettor.forms.forms import AddShowForm, DeleteForm, UpdateShowForm, NextEpForm
from gettor.classes import Downloader, ShowDetails

bp = Blueprint('show', __name__)
g_show = 0
dnl = Downloader()


def global_cleanups():
    print("cleanup")
    global g_show
    global dnl
    g_show = 0
    dnl.html = None
    dnl.tries = 0
    dnl.show = None


def get_details_helper(show):
    show.show_details = ShowDetails(show)
    show.show_details.update_details()


@bp.route('/')
def index():
    if g.user:
        global_cleanups()
        query = db.session.query(Show).filter_by(author_id=g.user.id)
        shows = query.all()
        for show in shows:
            get_details_helper(show)
        return render_template('show/index.html', shows=shows)
    else:
        flash("User must be logged in")
        return redirect(url_for('auth.login'))


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    global_cleanups()
    form = AddShowForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            flash('Add show {} '.format(form.name.data))
            name = form.name.data
            error = None

            if not name:
                error = 'Show name is required.'

            if error is not None:
                flash(error)
            else:
                show = Show(name=name,
                            additional_search=form.additional_search.data,
                            season=form.season.data,
                            episode=form.episode.data,
                            author_id=g.user.id)
                maze_id = show.get_maze_link()
                db.session.add(show)
                db.session.commit()
                if maze_id > 0:
                    show_to_maze = ShowToTvmaze(maze_id, show.id)
                    db.session.add(show_to_maze)
                    db.session.commit()
                dnl_url = url_for('show.download', id=str(show.id))
                return redirect(dnl_url)
    else:
        form.season.data = 1
        form.episode.data = 1

    return render_template('show/add_show.html', title='Add Show', form=form)


def get_show(id, check_author=True) -> Show:
    curr_show = db.session.query(Show).filter_by(id=id).first()
    if curr_show is None:
        abort(404, "Show id {0} doesn't exist.".format(id))

    if check_author and curr_show.author_id != g.user.id:
        abort(403)

    return curr_show


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    global_cleanups()
    curr_show = get_show(id)
    form_update = UpdateShowForm()
    form_delete = DeleteForm()
    if form_update.validate_on_submit():
        flash('update show {} '.format(form_update.name.data))
        name = form_update.name.data
        additional_search = form_update.additional_search.data
        season = form_update.season.data
        episode = form_update.episode.data
        error = None

        if not name:
            error = 'Show Name is required.'
        if error is not None:
            flash(error)
        else:
            curr_show.name = name
            curr_show.additional_search = additional_search
            curr_show.season = season
            curr_show.episode = episode
            db.session.commit()
            dnl_url = url_for('show.download', id=id)
            return redirect(dnl_url)
    elif form_delete.validate_on_submit() and form_delete.delete.data:
        flash('deleted show {} '.format(curr_show.name))
        delete_id(id)
        return redirect(url_for('index'))
    else:
        form_update.name.data = curr_show.name
        form_update.additional_search.data = curr_show.additional_search
        form_update.season.data = curr_show.season
        form_update.episode.data = curr_show.episode
    return render_template('show/update.html', title='Update Show', form_update=form_update, form_del=form_delete)


@bp.route('/<int:id>/download', methods=('GET', 'POST'))
@login_required
def download(id):
    global g_show
    global dnl
    show = get_show(id)
    if g_show != id:
        g_show = id
        dnl.load_show(show)
    get_details_helper(show)
    formnextep = NextEpForm()
    url_to_do = None
    if request.method == 'POST':
        if formnextep.validate_on_submit():
            if formnextep.download.data:
                flash('episode downloaded')
                #webbrowser.open_new_tab(dnl.curr_url[0])
                print("dnl22:" + dnl.curr_url[0])
                url_to_do = dnl.curr_url[0]
                show.step()
                dnl.load_show(show)
                dnl.download_episode()
                db.session.commit()
                # return redirect(url_to_do)

            elif formnextep.next.data:
                flash('next episode')
                show.step()
                dnl.load_show(show)
                dnl.download_episode()
                db.session.commit()

            elif formnextep.next_url.data:
                tries = dnl.tries
                # dnl.next_try()
                dnl.download_episode(next_try=1)

                if tries == dnl.tries:
                    flash('No Next link')
                else:
                    flash('Next link for this episode')

            elif formnextep.prev_url.data:
                tries = dnl.tries

                # dnl.next_try()
                dnl.download_episode(next_try=-1)
                if tries == dnl.tries:
                    flash('No Previous link')
                else:
                    flash('previous link for this episode')
    if dnl.curr_url is None:
        dnl.download_episode()

    return render_template('show/download.html', title='Download Show', show=show, formnextep=formnextep,
                           curr_url=dnl.curr_url, url_to_do=url_to_do)


def delete_id(id):
    global_cleanups()
    db.session.query(Show).filter_by(id=id).delete()
    db.session.commit()
    return
