FROM kbase/kbase:sdkbase.latest
MAINTAINER KBase Developer
# -----------------------------------------

# Insert apt-get instructions here to install
# any required dependencies for your module.

# RUN apt-get update

RUN sudo apt-get install python-dev libffi-dev libssl-dev \
    && pip install pyopenssl ndg-httpsclient pyasn1 --upgrade \
    && pip install requests --upgrade \
    && pip install 'requests[security]' --upgrade \
    && pip install requests_toolbelt --upgrade \
    && pip install semver \
    && ( [ $(pip show filemagic|grep -c filemagic) -eq 0 ] || pip uninstall -y filemagic ) \
    && pip install python-magic \
    && pip install ftputil \
    && pip install ipython \
    && sudo apt-get install nano
# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R 777 /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
