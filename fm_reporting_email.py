# -*- coding: utf-8 -*-

__version__ = "0.1.0"

# import libraries
import argparse
import os
import sys
import fm_tools
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import pandas
import datetime
from dateutil.relativedelta import relativedelta

# from __future__ import print_function
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.message import EmailMessage

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Notes
"""
Email functionality utilizes gmail oauth2 authentication
This requires 
1) setting up a project in "Google Cloud"
2) creating a client for the project and downloading the credentials json (client id+secret)
3) adding the scope for gmail sending "../auth/gmail.send"
4) enabling the gmail api for the project
5) linking a (test) user to utilize the client

online examples for implementation in python, and google/python error messaging help navigate the outlined steps
https://developers.google.com/workspace/gmail/api/guides/sending#python
https://stackoverflow.com/questions/73256179/how-to-send-email-with-attachment-through-gmail-api
https://stackoverflow.com/questions/37201250/sending-email-via-gmail-python

a token.json and a credential.json (not tracked in repository) are needed for email functionality
"""


# constants
credentials = {
    "ip": "https://10.140.180.26",
    "user": "Python",
    "password": "python",
}
email_keys = ["ToGeneral", "ToEngineers", "ToChris", "From", "CC"]

# collect email list


def collect_email_list():
    email_form = fm_tools.pull_the_table(
        credentials=credentials,
        database="MICE",
        layout="Error_List",
        table_keys=email_keys,
    )
    email_list = list(
        set(
            [
                [i for i in v["ToGeneral"].split()]
                + [i for i in v["ToEngineers"].split()]
                + [i for i in v["ToChris"].split()]
                + [i for i in v["From"].split()]
                + [i for i in v["CC"].split()]
                for k, v in email_form.items()
            ][0]
        )
    )
    return email_list


# collect error reports


def collect_error_reports():
    error_dict = fm_tools.pull_the_table(
        credentials=credentials,
        database="MICE",
        layout="Rigs_Error_Log",
        table_keys=None,
    )
    error_df = pandas.DataFrame(error_dict).transpose()
    return error_df


def build_summary_sheets(df, output_path="report"):
    # "all errors" list of all records sort by "error_type", "Component", "error_status"
    all_errors = df.sort_values(by=["error_type", "Component", "error_status"])
    # fill in blank error types
    all_errors.loc[all_errors["error_type"] == "", "error_type"] = "unknown"
    # use CreationTimestamp to populate entries without Experimental_Dates
    all_errors.loc[
        all_errors["Plethysmography::Experimental_Date"] == "",
        "Plethysmography::Experimental_Date",
    ] = pandas.to_datetime(
        all_errors[all_errors["Plethysmography::Experimental_Date"] == ""][
            "CreationTimestamp"
        ]
    ).dt.date
    # convert to datetime
    all_errors.loc[:, "Plethysmography::Experimental_Date"] = pandas.to_datetime(
        all_errors["Plethysmography::Experimental_Date"], format="mixed", dayfirst=False
    )
    all_errors["error_type_subcategory"] = all_errors[
        [
            "error_type",
            "Biological Error",
            "Human Error",
            "Component",
            "Bell Housing Error",
            "Connectivity Error",
            "ECG Error",
            "Facemask Error",
            "Software Error",
        ]
    ].apply(lambda row: "|".join(i for i in row if i), axis=1)

    all_errors["week of the year"] = pandas.to_datetime(
        pandas.to_datetime(all_errors["Plethysmography::Experimental_Date"])
        .dt.isocalendar()
        .year.astype(str)
        + "-W"
        + pandas.to_datetime(all_errors["Plethysmography::Experimental_Date"])
        .dt.isocalendar()
        .week.astype(str)
        .str.zfill(2)
        + "-1",
        format="%Y-W%W-%w",
    )

    last_month = all_errors[
        all_errors["Plethysmography::Experimental_Date"]
        >= datetime.datetime.now() - relativedelta(months=1)
    ]
    # summary sheets (recommend filter for last month)

    # "facemask" filter df.Component=="Facemask", aggregate by day > "Component" (count) (make graphs if possible, try other aggregates if possible)
    facemask = (
        last_month[["Component", "Plethysmography::Experimental_Date", "EUID"]][
            last_month["Component"] == "Facemask"
        ]
        .groupby(["Component", "Plethysmography::Experimental_Date"], as_index=False)
        .count()
    )
    # "rig" filter by date range, aggregate by "Plethysmography::Rig'" > "Component" (count)
    rig = (
        last_month[["Component", "error_type", "Plethysmography::Rig", "EUID"]]
        .groupby(["Plethysmography::Rig", "error_type", "Component"], as_index=False)
        .count()
    )
    # create summary xlsx
    writer = pandas.ExcelWriter(output_path + ".xlsx", engine="xlsxwriter")
    all_errors.to_excel(writer, sheet_name="all_errors", index=False)
    last_month.to_excel(writer, sheet_name="last_month", index=False)
    facemask.to_excel(writer, sheet_name="facemask", index=False)
    rig.to_excel(writer, sheet_name="rig", index=False)
    writer.close()

    # prepare graphs
    now = datetime.datetime.now()
    iso_week = pandas.to_datetime(
        f"{now.isocalendar().year}-W{now.isocalendar().week}-1", format="%Y-W%W-%w"
    ).date()
    iso_week_minus_8wks = iso_week - datetime.timedelta(weeks=8)
    iso_week_list = pandas.date_range(
        start=iso_week_minus_8wks, end=iso_week, freq=datetime.timedelta(days=7)
    )
    xminimum = iso_week_minus_8wks - datetime.timedelta(days=1)
    xmaximum = iso_week + datetime.timedelta(days=1)
    all_errors_last_8_weeks = all_errors[
        all_errors["week of the year"].dt.date >= iso_week_minus_8wks
    ]
    error_count = (
        all_errors_last_8_weeks[["error_type", "week of the year", "EUID"]]
        .groupby(by=["error_type", "week of the year"], as_index=False)
        .count()
    )
    error_subcategory_count = (
        all_errors_last_8_weeks[
            ["error_type_subcategory", "error_type", "week of the year", "EUID"]
        ]
        .groupby(
            by=["error_type_subcategory", "error_type", "week of the year"],
            as_index=False,
        )
        .count()
    )
    pdf_filename = output_path + ".pdf"
    with PdfPages(pdf_filename) as pdf:
        print("error graph")
        pivot = (
            error_count.pivot(
                index="week of the year", columns="error_type", values="EUID"
            )
            .reindex(index=iso_week_list)
            .fillna(0)
        )
        print(pivot)
        graph = pivot.plot(kind="line")
        graph.legend(
            fontsize=6, loc="upper left", bbox_to_anchor=(-0.10, -0.35), ncol=2
        )
        graph.set_title("Weekly count of errors", fontsize=10)
        graph.set_ylabel("count", fontsize=10)
        graph.set_ylim(bottom=0)
        graph.set_xlim(left=xminimum, right=xmaximum)
        graph.xaxis.set_major_locator(
            mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)
        )
        graph.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        plt.xticks(rotation=45)
        plt.minorticks_off()
        plt.subplots_adjust(bottom=0.5)
        pdf.savefig()
        plt.close()

        for e in error_count["error_type"].unique():
            print(f"error subcategory graph- {e}")
            if (
                error_subcategory_count[
                    error_subcategory_count["error_type"] == e
                ].shape[0]
                > 0
            ):
                pivot = (
                    error_subcategory_count[error_subcategory_count["error_type"] == e]
                    .pivot(
                        index="week of the year",
                        columns="error_type_subcategory",
                        values="EUID",
                    )
                    .reindex(index=iso_week_list)
                    .fillna(0)
                )
                print(pivot)
                graph = pivot.plot(
                    kind="line", title="weekly count of errors", label="count"
                )

                graph.legend(
                    fontsize=5, loc="upper left", bbox_to_anchor=(-0.10, -0.35), ncol=2
                )
                graph.set_title("Weekly count of errors", fontsize=10)
                graph.set_ylabel("count", fontsize=10)
                graph.set_ylim(bottom=0)
                graph.set_xlim(left=xminimum, right=xmaximum)
                graph.xaxis.set_major_locator(
                    mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)
                )
                graph.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
                plt.xticks(rotation=45)
                plt.minorticks_off()
                plt.subplots_adjust(bottom=0.5)
                pdf.savefig()
                plt.close()

        for e in error_subcategory_count["error_type_subcategory"].unique():
            print(f"error subcategory solo graph - {e}")
            if (
                error_subcategory_count[
                    error_subcategory_count["error_type_subcategory"] == e
                ].shape[0]
                > 0
            ):
                graph = error_subcategory_count[
                    error_subcategory_count["error_type_subcategory"] == e
                ].plot(x="week of the year", y="EUID", title=e, kind="scatter", label=e)
                graph.legend(
                    fontsize=6, loc="upper left", bbox_to_anchor=(-0.10, -0.35), ncol=2
                )
                graph.set_title(e, fontsize=10)
                graph.set_ylabel("count", fontsize=10)
                graph.set_ylim(bottom=0)
                graph.set_xlim(left=xminimum, right=xmaximum)
                graph.xaxis.set_major_locator(
                    mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)
                )
                graph.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
                plt.xticks(rotation=45)
                plt.minorticks_off()
                plt.subplots_adjust(bottom=0.5)
                pdf.savefig()
                plt.close()


# send email
def get_gmail_credentials():
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("attempting to refresh token")
            creds.refresh(Request())
        else:
            print("non-refreshable token")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def send_message(
    messageBody: str, subject: str, to_email: list, attachments: list = None
):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id"""

    creds = get_gmail_credentials()
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()

        message.set_content(messageBody)

        if attachments:
            for attachment in attachments:
                with open(attachment, "rb") as content_file:
                    content = content_file.read()
                    message.add_attachment(
                        content,
                        maintype="application",
                        subtype=(attachment.split(".")[1]),
                        filename=attachment,
                    )

        message["To"] = ", ".join(to_email)
        message["From"] = "ward.chris.s@gmail.com"
        message["Subject"] = subject
        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}

        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser("FM_Reporting_Email")
    parser.add_argument("-t", "--test", action="store_true")
    parsed_args = parser.parse_args()

    args = sys.argv.copy()

    if not parsed_args.test:
        print("\ncollecting emails >>")
        email_list = collect_email_list()
    else:
        email_list = ["ward.chris.s@gmail.com"]

    print(email_list)
    print("\ncollecting error info >>")
    error_df = collect_error_reports()
    # print(error_df)
    print(error_df.columns)
    build_summary_sheets(error_df)
    print("summary xlsx generated -> report.xlsx")

    print("sending email")
    send_message(
        messageBody="Rig Error Reporting test_message - Please see the attached Error Summary (xlsx file). Please notify C Ward or S Lusk if modifications to the xlsx report or email body text are desired. Anticipated email schedule will be weekly on Friday ~7am.",
        subject=f"Rig Error Reporting Summary - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}",
        to_email=email_list,
        attachments=["report.xlsx", "report.pdf"],
    )
    print("cleaning up")
    if os.path.exists("report.xlsx"):
        os.remove("report.xlsx")
    if os.path.exists("report.pdf"):
        os.remove("report.pdf")
    print("!!! finished !!!")
