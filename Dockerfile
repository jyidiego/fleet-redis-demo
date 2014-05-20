FROM orchardup/python:2.7
ADD . /code
WORKDIR /code
RUN pip install redis flask docker-py ipython pytz
RUN apt-get update
RUN apt-get -y install libssl-dev git curl wget ca-certificates build-essential mercurial socat libffi-dev
RUN git clone https://github.com/sstephenson/rbenv.git $HOME/.rbenv
ENV PATH $PATH:$HOME/.rbenv/bin:/usr/local/go/bin
ENV GOPATH /usr/local/go/
RUN echo 'eval "$(rbenv init -)"' >> /.bashrc
RUN git clone https://github.com/sstephenson/ruby-build.git $HOME/.rbenv/plugins/ruby-build
RUN rbenv install 2.0.0-p247
RUN curl -L https://github.com/orchardup/fig/releases/download/0.4.1/linux > /usr/local/bin/fig
RUN chmod +x /usr/local/bin/fig
RUN wget --no-verbose https://go.googlecode.com/files/go1.2.src.tar.gz
RUN tar -v -C /usr/local -xzf go1.2.src.tar.gz
RUN cd /usr/local/go/src && ./make.bash --no-clean 2>&1
RUN cd /code
RUN git clone https://github.com/coreos/fleet.git
RUN cd /code/fleet && ./build 2>&1
RUN git clone https://github.com/jplana/python-etcd.git
RUN cd /code/python-etcd && python ./setup.py install
