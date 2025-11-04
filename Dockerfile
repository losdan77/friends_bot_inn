FROM python:3.12

RUN mkdir /friends_bot

WORKDIR /friends_bot

COPY requeriments.txt .

RUN pip install -r requeriments.txt

COPY . .

RUN chmod a+x /friends_bot/*.sh

CMD [ "python", "main.py" ]