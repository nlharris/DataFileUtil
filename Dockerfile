FROM kbase/kbase:sdkbase.latest
MAINTAINER KBase Developer
# -----------------------------------------

# Insert apt-get instructions here to install
# any required dependencies for your module.

# RUN apt-get update

RUN sudo apt-get install python-dev libffi-dev libssl-dev
RUN pip install cffi --upgrade
RUN pip install pyopenssl --upgrade
RUN pip install ndg-httpsclient --upgrade
RUN pip install pyasn1 --upgrade
RUN pip install requests --upgrade \
    && pip install 'requests[security]' --upgrade \
    && pip install requests_toolbelt --upgrade \
    && pip install semver \
    && ( [ $(pip show filemagic|grep -c filemagic) -eq 0 ] || pip uninstall -y filemagic ) \
    && pip install python-magic \
    && pip install ftputil \
    && pip install ipython==5.3.0 \
    && sudo apt-get install nano
# -----------------------------------------

RUN sudo apt-get update \
    && yes '' | sudo apt-get -y upgrade openssl

RUN sudo apt-get install pigz
RUN pip install bz2file

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
