import http.cookiejar as cookielib
import json
import logging
import os
import re

import requests

# Set up logging
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=LOGLEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()


class SumoLogicCSE:
    """
    A class to interact with the Sumo Logic Cloud SIEM API.
    """

    def __init__(
        self,
        accessId=os.environ.get("SUMO_ACCESS_ID"),
        accessKey=os.environ.get("SUMO_ACCESS_KEY"),
        endpoint="https://api.sumologic.com/api/sec",
        caBundle=None,
        cookieFile="cookies.txt",
    ):
        """
        Initialize the SumoLogicCSE object.

        :param accessId: Sumo Logic access ID. Defaults to SUMO_ACCESS_ID env var.
        :param accessKey: Sumo Logic access key. Defaults to SUMO_ACCESS_KEY env var.
        :param endpoint: API endpoint. Defaults to 'https://api.sumologic.com/api/sec'.
        :param caBundle: CA bundle for SSL verification
        :param cookieFile: File to store cookies
        """
        self.session = requests.Session()
        self.session.auth = (accessId, accessKey)
        self.DEFAULT_VERSION = "v1"
        self.session.headers = {
            "content-type": "application/json",
            "accept": "application/json",
        }
        if caBundle is not None:
            self.session.verify = caBundle
        cj = cookielib.FileCookieJar(cookieFile)
        self.session.cookies = cj

        if endpoint is None:
            self.endpoint = "https://api.sumologic.com/api/sec"
        elif re.match("au|fra|mum|us2|mon|dub|tky", endpoint):
            self.endpoint = "https://api." + endpoint + ".sumologic.com/api/sec"
        elif re.match("prod|us1", endpoint):
            self.endpoint = "https://api.sumologic.com/api/sec"
        else:
            self.endpoint = endpoint
        if self.endpoint[-1:] == "/":
            raise Exception("Endpoint should not end with a slash character")
        logger.debug("endpoint: " + str(self.endpoint))
        logger.debug("accessid: " + accessId[0:3] + "####" + accessId[12:-1])

    def get_versioned_endpoint(self, version):
        """
        Get the versioned endpoint URL.

        :param version: API version
        :return: Versioned endpoint URL
        """
        return self.endpoint + f"/{version}"

    def delete(self, method, params=None, version=None):
        """
        Send a DELETE request.

        :param method: API method
        :param params: Request parameters
        :param version: API version
        :return: Response object
        """
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.delete(endpoint + method, params=params)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def get(self, method, params=None, version=None):
        """
        Send a GET request.

        :param method: API method
        :param params: Request parameters
        :param version: API version
        :return: Response object
        """
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.get(endpoint + method, params=params)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def post(self, method, params, headers=None, version=None):
        """
        Send a POST request.

        :param method: API method
        :param params: Request parameters
        :param headers: Request headers
        :param version: API version
        :return: Response object
        """
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.post(
            endpoint + method, data=json.dumps(params), headers=headers
        )
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def post_file(self, method, params, headers=None, version=None):
        """
        Handle file uploads via a separate POST request.

        :param method: API method
        :param params: Request parameters
        :param headers: Request headers
        :param version: API version
        :return: Response object
        """
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        post_params = {"merge": params["merge"]}
        with open(params["full_file_path"], "rb") as f:
            file_data = f.read()
        files = {"file": (params["file_name"], file_data)}
        r = requests.post(
            endpoint + method,
            files=files,
            params=post_params,
            auth=(self.session.auth[0], self.session.auth[1]),
            headers=headers,
        )
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def put(self, method, params, headers=None, version=None):
        """
        Send a PUT request.

        :param method: API method
        :param params: Request parameters
        :param headers: Request headers
        :param version: API version
        :return: Response object
        """
        version = version or self.DEFAULT_VERSION
        endpoint = self.get_versioned_endpoint(version)
        r = self.session.put(
            endpoint + method, data=json.dumps(params), headers=headers
        )
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def get_insights_all(self, q=None, nextPageToken=None):
        """
        Retrieve all insights.

        :param q: Query parameter
        :param nextPageToken: Token for the next page
        :return: JSON response
        """
        params = {"q": q, "nextPageToken": nextPageToken}
        response = self.get("/insights/all", params)
        return json.loads(response.text)

    def get_insights(self, q=None, max_pages=5):
        """
        Retrieve insights with pagination.

        :param q: Query parameter
        :param max_pages: Maximum number of pages to retrieve
        :return: List of insights
        """
        insights = []
        pages = 0
        next_page_token = None
        while pages < max_pages:
            pages += 1
            i = self.get_insights_all(q, next_page_token)
            if len(i["data"]["objects"]) > 0:
                insights = insights + i["data"]["objects"]
            else:
                logger.debug("no results")

            next_page_token = i["data"]["nextPageToken"]

            if next_page_token is None:
                logger.debug(
                    str(len(insights)) + " insights at last page: " + str(pages)
                )
                break
        return insights

    def get_insights_list(self, q=None, offset=0, limit=20):
        """
        Retrieve a list of insights with offset and limit.

        :param q: Query parameter
        :param offset: Offset for pagination
        :param limit: Limit for pagination
        :return: JSON response
        """
        params = {"q": q, "offset": offset, "limit": limit}
        response = self.get("/insights", params)
        return json.loads(response.text)

    def query_insights(self, q=None, offset=0, limit=20):
        """
        Query insights with pagination.

        :param q: Query parameter
        :param offset: Offset for pagination
        :param limit: Limit for pagination
        :return: List of insights
        """
        insights = []
        pages = 0
        batchsize = 20 if limit > 20 else limit

        remaining = limit
        while remaining > 0:
            i = self.get_insights_list(q, offset=pages, limit=batchsize)
            logger.debug(
                "batch:"
                + str(pages)
                + " remaining: "
                + str(remaining)
                + " batchsize:"
                + str(batchsize)
            )
            logger.debug("returned: " + str(len(i["data"]["objects"])))
            if len(i["data"]["objects"]) > 0:
                insights = insights + i["data"]["objects"]
                remaining = remaining - len(i["data"]["objects"])
            else:
                logger.debug("no results")
                remaining = 0

            if not i["data"]["hasNextPage"]:
                logger.debug(
                    str(len(insights))
                    + " insights at last page: "
                    + str(len(i["data"]["objects"]))
                )
                break
            pages += batchsize
            batchsize = 20 if remaining > 20 else remaining
        return insights

    def get_insight(self, insight_id):
        """
        Retrieve a specific insight by ID.

        :param insight_id: Insight ID
        :return: JSON response
        """
        response = self.get(f"/insights/{insight_id}")
        return json.loads(response.text)

    def get_insight_statuses(self):
        """
        Retrieve all insight statuses.

        :return: JSON response
        """
        response = self.get("/insight-status")
        return json.loads(response.text)

    def update_insight_resolution_status(self, insight_id, resolution, status):
        """
        Update the resolution status of an insight.

        :param insight_id: Insight ID
        :param resolution: Resolution status
        :param status: Status
        :return: JSON response
        """
        body = {"resolution": resolution, "status": status}
        response = self.put(f"/insights/{insight_id}/status", body)
        return json.loads(response.text)

    def add_insight_comment(self, insight_id, comment):
        """
        Add a comment to an insight.

        :param insight_id: Insight ID
        :param comment: Comment text
        :return: JSON response
        """
        body = {"body": comment}
        response = self.post(f"/insights/{insight_id}/comments", body)
        return json.loads(response.text)

    def get_rules(self, q=None, offset=0, limit=20):
        """
        Retrieve rules with optional query and pagination.

        :param q: Query parameter for filtering rules
        :param offset: Offset for pagination
        :param limit: Limit for pagination (max 100)
        :return: JSON response
        """
        params = {"q": q, "offset": offset, "limit": limit}
        response = self.get("/rules", params)
        return json.loads(response.text)

    def get_rule(self, rule_id):
        """
        Retrieve a specific rule by ID.

        :param rule_id: Rule ID
        :return: JSON response
        """
        response = self.get(f"/rules/{rule_id}")
        return json.loads(response.text)

    def query_rules(self, q=None, offset=0, limit=20):
        """
        Query rules with pagination handling.

        :param q: Query parameter for filtering rules
        :param offset: Offset for pagination
        :param limit: Limit for pagination
        :return: List of rules
        """
        rules = []
        pages = 0
        batchsize = min(limit, 20) if limit > 20 else limit

        remaining = limit
        while remaining > 0:
            r = self.get_rules(q, offset=pages, limit=batchsize)
            logger.debug(f"batch:{pages} remaining:{remaining} batchsize:{batchsize}")
            logger.debug(f"returned: {len(r['data']['objects'])}")

            if len(r["data"]["objects"]) > 0:
                rules.extend(r["data"]["objects"])
                remaining -= len(r["data"]["objects"])
            else:
                logger.debug("no results")
                remaining = 0

            if not r["data"]["hasNextPage"]:
                logger.debug(f"{len(rules)} rules at last page")
                break

            pages += batchsize
            batchsize = min(20, remaining)

        return rules
