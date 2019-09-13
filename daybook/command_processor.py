import argparse
import sys


class CommandProcessor(object):
    def usage(self):
        return """
        commands:
        
        create_project 
        list_entries 
        """

    def parse_args(self):
        parser = argparse.ArgumentParser(description="A git-based journal called daybook", usage=self.usage())
        parser.add_argument("command", help="subcommand to run")
        parser.add_argument("--project_name", help="the daybook name")
        print("subcommand is {}".format((sys.argv[1:3])))
        args = parser.parse_args(sys.argv[1:3])
        project_name = args.project_name
        print("project name is {}".format(project_name))
        if not hasattr(self, args.command):
            print('Unrecognized command: {}'.format(args.command))
            parser.print_help()
            exit(1)

        return (args.project_name, args.command, getattr(self, args.command)())

    def create_project(self):
        """
        Parse the create project subcommand
        Return a tuple of (subcommand, args)
        :return:
        """
        parser = argparse.ArgumentParser(description='create a new daybook')
        parser.add_argument('-b', '--basedir', help="The base directory for the daybook to live beneath")
        return parser.parse_args(sys.argv[2:])

    def list_entries(self):
        parser = argparse.ArgumentParser(description='list existing entries')
        parser.add_argument('-m', '--max_entries', help="The max number of entries")
        parser.add_argument('-t', '--with_tags', help="Return only entries having tags.  Comma-delimited")
        parser.add_argument('-T', '--with_text', help="Return only entries having text.  Comma-delimited")
        parser.add_argument('-b', '--after_date', help="Return only entries written after the given date.")
        parser.add_argument('-a', '--before_date', help="Return only entries written before the given date.")
        return parser.parse_args(sys.argv[2:])

