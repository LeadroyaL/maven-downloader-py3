#!/usr/bin/env python3
# coding=utf-8
import argparse
import os
import shutil
import requests
import xml.etree.ElementTree as ET


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--library', required=True, help='the library in format: groupId:artifactId[:version]')
    parser.add_argument('-u', '--maven_urls', action='append', required=True, help='mavenCentral/jcenter/google or custom url')
    parser.add_argument('-o', '--output', required=False, help='the library output directory', default=".")
    return parser.parse_args()


class MavenLib(object):
    def __init__(self, groupId: str, artifactId: str, version: str = None):
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.packaging = "jar"

    @classmethod
    def parseDescription(cls, description: str):
        _ = description.split(':')
        if len(_) > 2:
            return MavenLib(_[0], _[1], _[2])
        else:
            _ret = MavenLib(_[0], _[1])
            _ret.choose_version()
            return _ret

    def relative_metadata(self):
        x = self.groupId.split(".")
        x.extend([self.artifactId, "maven-metadata.xml"])
        return "/".join(x)

    def relative_pom_path(self):
        return self._relative_path("pom")

    def relative_jar_path(self):
        return self._relative_path(self.packaging)

    def _relative_path(self, suffix):
        x = self.groupId.split(".")
        x.extend([self.artifactId, self.version, "%s-%s.%s" % (self.artifactId, self.version, suffix)])
        return "/".join(x)

    def choose_version(self) -> None:
        et = ET.fromstring(downloader.download_metadata(self))
        xmlns = et.tag[0: et.tag.find('}') + 1] if et.tag.startswith('{') else ""
        versioning = et.find("%sversioning" % xmlns)
        latest = versioning.find('%slatest' % xmlns)
        release = versioning.find('%srelease' % xmlns)
        if latest:
            print('[latest]', latest.text)
        if release:
            print('[release]', release.text)
        versions = versioning.find('%sversions' % xmlns)
        i = 0
        for version in versions:
            print('[%d]' % i, version.text)
            i += 1
        choice = input("input the choice (latest/release/index):\n")
        if choice == 'latest':
            choice = latest.text
        elif choice == 'release':
            choice = release.text
        else:
            choice = versions[int(choice)].text
        print(choice)
        if choice is None:
            raise RuntimeError("cannot determine version")
        self.version = choice

    def __eq__(self, other):
        return (self.groupId == other.groupId
                and self.artifactId == other.artifactId
                and self.version == other.version)

    def __ne__(self, other):
        return (self.groupId != other.groupId or
                self.artifactId != other.artifactId or
                self.version != other.version)

    def __cmp__(self, other):
        t1 = "%s:%s:%s" % (self.groupId, self.artifactId, self.version)
        t2 = "%s:%s:%s" % (other.groupId, other.artifactId, other.version)

        if t1 > t2:
            return 1
        if t1 < t2:
            return -1
        return 0

    def __repr__(self):
        return "%s:%s:%s" % (self.groupId, self.artifactId, self.version)


class DepNode:
    def __init__(self, base_info: MavenLib):
        self.base_info: MavenLib = base_info
        self.dependencies = []

    def __repr__(self):
        return "%s ->\n %s" % (self.base_info.__repr__(), ','.join(self.dependencies))


class Downloader:
    def __init__(self, repos, output_dir):
        self.repos = self._format_repos(repos)
        self.output_dir = output_dir
        self.remote_maven_files = []
        self.local_maven_files = []
        self.session = requests.Session()

    @staticmethod
    def _format_repos(urls):
        _repos = set()
        for url in urls:
            if url == 'google':
                _repos.add("https://maven.google.com/")
            elif url == 'jcenter':
                _repos.add("https://jcenter.bintray.com/")
            elif url == 'mavenCentral':
                _repos.add("https://repo1.maven.org/maven2/")
            elif url.endswith('/'):
                _repos.add(url)
            else:
                _repos.add(url + '/')
        return _repos

    def check_local_file(self):
        if not os.path.isdir(downloader.output_dir):
            return
        for groupId in os.listdir(downloader.output_dir):
            if not os.path.isdir(downloader.output_dir + os.sep + groupId):
                continue
            for artifactId in os.listdir(downloader.output_dir + os.sep + groupId):
                if not os.path.isdir(downloader.output_dir + os.sep + groupId + os.sep + artifactId):
                    continue
                for f in os.listdir(downloader.output_dir + os.sep + groupId + os.sep + artifactId):
                    if f.find('-') != -1:
                        version = os.path.splitext(f)[0].rsplit('-', 1)[1]
                        self.local_maven_files.append(MavenLib(groupId, artifactId, version))

    def _download_str(self, relative_resource):
        for repo in self.repos:
            try:
                r = self.session.get(repo + relative_resource)
                if r.status_code == 200:
                    print("%d:%s" % (r.status_code, r.url))
                    return r.text
                else:
                    print("%d:%s" % (r.status_code, r.url))
            except Exception as e:
                print(e)
        return None

    def download_metadata(self, lib: MavenLib) -> str:
        return self._download_str(lib.relative_metadata())

    def download_pom(self, lib: MavenLib) -> str:
        _ = self._download_str(lib.relative_pom_path())
        self.remote_maven_files.append(lib)
        return _

    @staticmethod
    def mkdir():
        if not os.path.isdir(downloader.output_dir):
            os.makedirs(downloader.output_dir)

    def download_file(self, relative_path, output_path):
        _dir = os.path.dirname(self.output_dir + os.sep + output_path)
        if not os.path.isdir(_dir):
            os.makedirs(_dir)
        for repo in self.repos:
            try:
                url = repo + relative_path
                r = self.session.get(url, stream=True)
                if r.status_code == 200:
                    print("%d:%s" % (r.status_code, r.url))
                    with open(self.output_dir + os.sep + output_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    return True
                else:
                    print("%d:%s" % (r.status_code, r.url))
            except Exception as e:
                print(e)
        return False

    def download_dep_tree(self, _tree: DepNode):
        lib = _tree.base_info
        print("try to download", lib, lib.packaging)
        if lib in self.local_maven_files:
            print("local cache hit", lib)
        else:
            jar_path = lib.relative_jar_path()
            file_name = os.path.basename(jar_path)
            self.download_file(jar_path, os.sep.join([lib.groupId, lib.artifactId, file_name]))
        for dependency in _tree.dependencies:
            self.download_dep_tree(dependency)

    def resolve_dep_tree(self, _root: DepNode):
        pom_data = downloader.download_pom(_root.base_info)
        if pom_data is None:
            return
        et = ET.fromstring(pom_data)
        xmlns = et.tag[0: et.tag.find('}') + 1] if et.tag.startswith('{') else ""
        packaging = et.find('%spackaging' % xmlns)
        dependencies = et.find('%sdependencies' % xmlns)

        if packaging is not None:
            _root.base_info.packaging = packaging.text

        if dependencies is None:
            return
        for dependency in dependencies:
            scope = dependency.find("%sscope" % xmlns)
            if scope is not None:
                if scope.text == 'provided' or scope.text == 'test':
                    continue
            groupId = dependency.find("%sgroupId" % xmlns)
            artifactId = dependency.find("%sartifactId" % xmlns)
            version = dependency.find("%sversion" % xmlns)
            if groupId is None or artifactId is None or version is None:
                print("skip", groupId, artifactId, version)
            elif groupId.text.replace('${project.groupId}', '').find('$') != -1 or version.text.replace('${project.version}', '').find('$') != -1:
                print("skip", groupId.text, version.text)
            else:
                _m = MavenLib(groupId.text.replace('${project.groupId}', _root.base_info.groupId),
                              artifactId.text,
                              version.text.replace('${project.version}', _root.base_info.version))
                _root.dependencies.append(DepNode(_m))
        for dependency in _root.dependencies:
            _hit = False
            for remote_maven_file in self.remote_maven_files:
                if dependency.base_info == remote_maven_file:
                    # fix packaging info
                    dependency.base_info.packaging = remote_maven_file.packaging
                    _hit = True
                    break
            if _hit:
                print("remote cache hit", remote_maven_file)
                continue
            self.resolve_dep_tree(dependency)


args = parse_arg()
downloader = Downloader(args.maven_urls, args.output)
downloader.mkdir()
root = DepNode(MavenLib.parseDescription(args.library))
downloader.resolve_dep_tree(root)
downloader.check_local_file()
downloader.download_dep_tree(root)
