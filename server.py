"""The script runs the API server."""

from configparser import ConfigParser
import threading
import time

from flask import Flask, request
from flask_json import as_json
import psycopg2
import waitress


def database_query(psql_config, query):
    """Executes the PostgreSQL database query and returns the results and any
    database errors."""
    results = None
    errors = list()
    try:
        conn = psycopg2.connect(**psql_config)
        cur = conn.cursor()

        cur.execute(query)
        print("Query:", query)
        results = cur.fetchall()
        cur.close()

    except psycopg2.DatabaseError as err:
        errors.append(str(err))

    finally:
        if conn is not None:
            conn.close()

    return results, errors


class Server(threading.Thread):
    """Class for the API server."""

    APP = 'API_SERVER'

    def __init__(self, host="localhost", port=8000, psql_config=None):
        self.host = host
        self.port = port
        self.psql_config = psql_config
        self._app = self._configure_app()
        self._server = self._configure_server()
        super().__init__(target=self._server.run)

    def _configure_app(self):
        """Setup the app."""

        app = Flask(self.APP)
        app.config['JSON_ADD_STATUS'] = False

        @app.route('/query', methods=["POST"])
        @as_json
        def query():
            """Form the API response to the query. Returns the payload and the
            status code."""
            if request.json is None:
                return {"errors": ["No JSON body in request"]}, 400

            metadata, criteria, order_by, reverse, errors = self._extract_parameters(request.json)

            if errors:
                return {"errors": errors}, 400

            query = self._construct_select(metadata)
            if criteria:
                query += " " + self._construct_where(criteria)
            if order_by:
                query += " " + self._construct_order_by(order_by, reverse)
            query += ";"

            try:
                results, errors = database_query(self.psql_config, query)
                if errors:
                    return {"errors": errors}, 500
                return {"results": self._serialise_results(metadata, results)}
            except Exception as err:
                return {"errors": [str(err)]}, 400

        return app

    def _configure_server(self):
        """Setup the server."""
        return waitress.create_server(self._app, host=self.host, port=self.port)

    def shutdown(self):
        """Graceful shutdown of the server."""
        if self.is_alive:
            self._server.close()
        self.join(timeout=2)

    @staticmethod
    def _extract_parameters(json_query):
        """Extract the parameters from the JSON body, report any errors with its
        format."""
        metadata = json_query.get("metadata", None)
        criteria = json_query.get("criteria", dict())
        order_by = json_query.get("order_by", None)
        reverse = json_query.get("reverse", False)
        errors = list()

        if metadata is None:
            errors.append("Missing metadata in JSON body.")
        elif not isinstance(metadata, list):
            errors.append("The metadata parameter should be a list.")
        if not isinstance(criteria, dict):
            errors.append("The criteria parameter should be a JSON object.")
        else:
            for category, conditions in criteria.items():
                if isinstance(conditions, dict):
                    continue
                errors.append(
                    "The value for the criteria category %s "
                    "should be a JSON object." % category
                )
        if order_by and not isinstance(order_by, str):
            errors.append("The order_by parameter should be a string.")
        if reverse and not isinstance(reverse, bool):
            errors.append("The reverse parameter should be a string.")

        return metadata, criteria, order_by, reverse, errors

    @staticmethod
    def _construct_select(metadata):
        return "SELECT %s FROM metrics" % ", ".join(metadata)

    @staticmethod
    def _construct_where(criteria):
        requirements = list()
        for category, conditions in criteria.items():
            if "less than" in conditions:
                requirements.append("%s < %s" % (category, conditions["less than"]))
            if "more than" in conditions:
                requirements.append("%s > %s" % (category, conditions["more than"]))
        if not requirements:
            return ""
        return "WHERE %s" % " AND ".join(requirements)

    @staticmethod
    def _construct_order_by(order_by, reverse):
        return "ORDER BY %s %s" % (order_by, "DESC" if reverse else "ASC")

    @staticmethod
    def _serialise_results(metadata, results):
        data = list()
        for entry in results:
            data.append({category: value for category, value in zip(metadata, entry)})
        return data


def main(config_file):
    """Read the config and start the server."""

    # Get server and postgresql config
    config = ConfigParser()
    config.read(config_file)
    server_config = dict(config.items("server"))
    (host, port) = server_config["host"], server_config["port"]
    psql_config = dict(config.items("postgresql"))

    # Start the server
    print("Starting server, host %s on port %s" % (host, port))
    server = Server(host, port, psql_config)
    server.start()

    # Stop the server
    flag = False
    while not flag:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down server.")
            flag = True
            server.shutdown()


if __name__ == "__main__":
    main(config_file="config.ini")
