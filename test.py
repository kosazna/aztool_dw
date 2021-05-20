# import sqlite3
from sqlite3 import connect, Error
from contextlib import closing
from sqlite3.dbapi2 import paramstyle

ota_query = open("ota.sql").read()
shape_query = open("shape.sql").read()
locality_query = open("locality.sql").read()
fbound_query = open("fbound.sql").read()
update_overlaps_query = open("u_overlaps.sql").read()
overlaps_query = open("overlaps.sql").read()
update_geometry_query = open("u_geometry.sql").read()
geometry_query = open("geometry.sql").read()
update_logs = open("u_logs.sql").read()


class KtimaSQL:
    def __init__(self, db, meleti, mode) -> None:
        self.db = db
        self.meleti = meleti
        self.mode = mode

    def set_mode(self, mode):
        self.mode = mode

    def get_otas(self, company_name='NAMA'):
        params = {'meleti': self.meleti,
                  'company_name': company_name}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(ota_query, params)

                    return [row[0] for row in cur.fetchall()]
        except Error as e:
            print(str(e) + " from " + self.db)
            return []

    def get_shapes(self, ktima_type):
        params = {'meleti': self.meleti,
                  'ktima_type': ktima_type}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(shape_query, params)

                    return [row[0] for row in cur.fetchall()]
        except Error as e:
            print(str(e) + " from " + self.db)
            return []

    def get_locality(self):
        params = {'meleti': self.meleti}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(locality_query, params)

                    return cur.fetchall()
        except Error as e:
            print(str(e) + " from " + self.db)
            return []

    def get_fbound_docs(self):
        params = {'meleti': self.meleti}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(fbound_query, params)

                    return cur.fetchall()
        except Error as e:
            print(str(e) + " from " + self.db)
            return []

    def get_overlaps(self):
        params = {'meleti': self.meleti,
                  'mode': self.mode, }
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(overlaps_query, params)

                    return cur.fetchone()
        except Error as e:
            print(str(e) + " from " + self.db)

    def update_overlaps(self, check_date, decimals, astenot, asttom, pst):
        params = {'meleti': self.meleti,
                  'mode': self.mode,
                  'check_date': check_date,
                  'decimals': decimals,
                  'astenot': astenot,
                  'asttom': asttom,
                  'pst': pst}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(update_overlaps_query, params)
                    con.commit()

        except Error as e:
            print(str(e) + " from " + self.db)

    def get_geometry(self, shape):
        params = {'meleti': self.meleti,
                  'mode': self.mode,
                  'shape': shape}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(geometry_query, params)

                    return cur.fetchone()
        except Error as e:
            print(str(e) + " from " + self.db)

    def update_geometry(self, shape, check_date, has_probs, ota):
        params = {'meleti': self.meleti,
                  'mode': self.mode,
                  'shape': shape,
                  'check_date': check_date,
                  'has_probs': has_probs,
                  'ota': ota}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(update_geometry_query, params)
                    con.commit()

        except Error as e:
            print(str(e) + " from " + self.db)

    def update_logs(self, dt, user, action, comments):
        params = {'datetime': dt,
                  'user': user,
                  'meleti': self.meleti,
                  'action': action,
                  'comments': comments}
        try:
            with closing(connect(self.db)) as con:
                with closing(con.cursor()) as cur:
                    cur.execute(update_logs, params)
                    con.commit()

        except Error as e:
            print(str(e) + " from " + self.db)


ktima = KtimaSQL("D:/ktima.db", "KT5-17", "ktima")
print(ktima.update_logs("2021-05-20 15:16:06", 'azna', 'test', 'test'))
