from pecan import expose, abort, request
from pecan.secure import secure

from shaman.models import Project, Build
from shaman.auth import basic_auth
from shaman import models


class ProjectAPIController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
        else:
            request.context['project_id'] = self.project.id

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return list(
            set([r.ref for r in self.project.repos])
        )

    #TODO: we need schema validation on this method
    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        if not self.project:
            self.project = models.get_or_create(Project, name=self.project_name)
        build_url = request.json["build_url"]
        repo = Build.query.filter_by(build_url=build_url).first()
        if not repo:
            data = dict(
                project=self.project,
                ref=request.json["ref"],
                sha1=request.json["sha1"],
                flavor=request.json["flavor"],
            )
            repo = models.get_or_create(Build, **data)
        update_data = dict(
            status=request.json["status"],
            url=request.json.get("url", ""),
            extra=request.json.get("extra", dict()),
        )
        repo.update_from_json(update_data)
        return {}


class ProjectsAPIController(object):

    @expose('json')
    def index(self):
        resp = {}
        for project in Project.query.all():
            resp[project.name] = dict(
                refs=project.refs,
                sha1s=project.sha1s,
            )
        return resp

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectAPIController(project_name), remainder