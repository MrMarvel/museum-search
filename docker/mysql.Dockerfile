FROM mysql:8

# from project root

COPY ./services/frontend/dump.sql /docker-entrypoint-initdb.d/


#RUN (printf "[client]\nuser = %s\npassword = %s" "root" "ROOT") > ./supress_mysql.cnf

#RUN cat dump.sql | mysql --defaults-extra-file=./supress_mysql.cnf