import random
import smtplib
import sqlite3
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PyQt5 import QtWidgets, QtCore
from PyQt5 import uic
from PyQt5.QtCore import QSize, QDate
from PyQt5.QtGui import QImage, QPalette, QBrush, QPixmap
from PyQt5.QtWidgets import QWidget, QDialog, QPushButton, QLabel, QComboBox, QTableWidgetItem

mac = 'йцукенгшщзхъ фывапролджэё ячсмитьбю qwertyuiop asdfghjkl zxcvbnm 1 ; 2 3 4 5 6 7 8 9 0 .'
sql = sqlite3.connect('users.db')
cursor = sql.cursor()
print('[LOG] DB connect')


def good_login(login):
    global cursor
    print('[LOG] login checked')
    return len(login) > 4 and not cursor.execute(f"""
    select account from accounts where account = '{login}'
    """).fetchone()


def good_email(email):
    global cursor
    print('[LOG] email checked')
    return True if not cursor.execute(f"""
    select email from accounts where email = '{email}'
    """).fetchone() and email.count('@') == 1 and not email.endswith('@') else False


def good_password(password):
    print('[LOG] password checked')

    def ok(word):
        word = word.lower()
        for i in range(len(word) - 2):
            if mac.index(word[i]) + 2 == mac.index(word[i + 1]) + 1 == mac.index(word[i + 2]):
                return False
        return True

    if len(password) > 8:
        if password.lower() != password:
            if not password.replace('.', '').replace(';', '').isalpha() \
                    and not password.replace('.', '').replace(';', '').isdigit():
                if len(set(password.lower()) - set(mac)) == 0:
                    return True if ok(password) else False
    return False


class Doctor(QDialog):
    def __init__(self, doctorid, parent=None):
        try:

            self.doctorid = doctorid
            super(Doctor, self).__init__(parent)
            self.SelectedRow = 0
            self.parent = parent
            uic.loadUi('doctor.ui', self)
            self.ClientNowInRoom = False

            self.Abnormal.setEnabled(False)
            self.Alergy.setEnabled(False)
            self.Deff.setEnabled(False)
            self.other.setEnabled(False)

            self.Abnormal.setText('нет')
            self.Alergy.setText('нет')
            self.Deff.setText('нет')
            self.other.setText('нет')

            self.Image = QImage("бежевый.jpg")
            self.Image = self.Image.scaled(QSize(900, 900))
            self.palette = QPalette()
            self.palette.setBrush(10, QBrush(self.Image))
            self.setPalette(self.palette)

            self.table.cellClicked.connect(self.cell_was_clicked)
            self.start_session.clicked.connect(self.Start)
            self.end_session.clicked.connect(self.End)
            self.setWindowTitle('Время и дата')
            self.setModal(True)
            self.update(self.doctorid)
        except Exception as err:
            print("ERROR")
            print(err)

        try:
            self.logo.setPixmap(QPixmap('LOGO.png'))
        except FileNotFoundError:
            print('[ERROR REPORT] file "LOGO.png" not found')
        print('[LOG] exemplar "Doctor" class created successfully')

    def update(self, doctorid):
        try:
            self.name.setText(' '.join(
                cursor.execute(
                    f"""select surname, name, patronymic from specialists where id = {doctorid}""").fetchall()[
                    0]))
            Scheudule = cursor.execute(
                f"""select client_id, date, time from schedule where doctor_id = {doctorid}""").fetchall()
            ScheuduleToday = []
            for i in Scheudule:
                FormatDate = i[1].split('.')
                if int(FormatDate[0]) == date.today().day and int(FormatDate[1]) == date.today().month and int(
                        FormatDate[2]) == date.today().year:
                    ScheuduleToday.append(i)
            ScheuduleToday.sort(key=lambda x: (x[2].split(':')[0], x[2].split(':')[1]))
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels(
                ["Пациент", "Время", "Аллергия", "Жалобы", "Противопоказания", "Дополнительно", "Родился"])
            self.table.setRowCount(len(ScheuduleToday))
            Row = 0
            self.PeopleId = []
            for i in ScheuduleToday:
                self.PeopleId.append(i[0])
                FIO = ' '.join(
                    cursor.execute(f"select surname, name, patronymic from clients where id = {i[0]}").fetchall()[0])
                self.table.setItem(Row, 0, QTableWidgetItem(FIO))
                self.table.setItem(Row, 1, QTableWidgetItem(i[2]))
                Res = cursor.execute(
                    f"select allergy, abnormality, deffects, other from precautions where client_id = {i[0]}").fetchall()[
                    0]
                self.table.setItem(Row, 2, QTableWidgetItem(Res[0]))
                self.table.setItem(Row, 3, QTableWidgetItem(Res[1]))
                self.table.setItem(Row, 4, QTableWidgetItem(Res[2]))
                self.table.setItem(Row, 5, QTableWidgetItem(Res[3]))
                Res = cursor.execute(f"select birth from clients where id = {i[0]}").fetchall()[0][0]
                self.table.setItem(Row, 6, QTableWidgetItem(Res))
                Row += 1
            self.table.setFocusPolicy(QtCore.Qt.NoFocus)
            self.table.resizeColumnsToContents()
        except Exception as err:
            print("ERROR")
            print(err)

        print('[LOG] Update completed successful')

    def End(self):
        global cursor
        global sql
        try:
            if self.ClientNowInRoom:
                self.Abnormal.setEnabled(False)
                self.Alergy.setEnabled(False)
                self.Deff.setEnabled(False)
                self.other.setEnabled(False)
                N = ' '.join(cursor.execute(
                    f"select surname, name, patronymic from clients where id = {self.PeopleId[self.SelectedRow]}")
                             .fetchall()[0])
                cursor.execute(
                    f"UPDATE precautions SET allergy = '{str(self.Alergy.text())}',"
                    f" other = '{str(self.other.text())}',"
                    f" abnormality = '{str(self.Abnormal.text())}',"
                    f" deffects = '{str(self.Deff.text())}'"
                    f" WHERE client_id = {self.PeopleId[self.SelectedRow]}")
                cursor.execute("""""")
                self.ClientNowInRoom = False

                FormatTodayDate = '.'.join([str(date.today().day), str(date.today().month), str(date.today().year)])

                print(f'[LOG] Appointment end for {N}')
                cursor.execute(
                    f"""Delete from schedule where date = '{FormatTodayDate}' and client_id = {self.PeopleId[self.SelectedRow]} and doctor_id = {self.doctorid}""")
                self.update(self.doctorid)
                sql.commit()

                self.Abnormal.setText('нет')
                self.Alergy.setText('нет')
                self.Deff.setText('нет')
                self.other.setText('нет')


        except Exception as err:
            print(err)

    def Start(self):
        global cursor
        global sql
        try:
            if not self.ClientNowInRoom:
                print(self.PeopleId[self.SelectedRow])
                Data = cursor.execute(
                    f"""select allergy, abnormality, deffects, other from precautions where client_id = {self.PeopleId[self.SelectedRow]}""").fetchall()[
                    0]
                print(Data)
                self.Abnormal.setText(str(Data[1]))
                self.Alergy.setText(str(Data[0]))
                self.Deff.setText(str(Data[2]))
                self.other.setText(str(Data[3]))

                self.Abnormal.setEnabled(True)
                self.Alergy.setEnabled(True)
                self.Deff.setEnabled(True)
                self.other.setEnabled(True)
                N = ' '.join(cursor.execute(
                    f"select surname, name, patronymic from clients where id = {self.PeopleId[self.SelectedRow]}")
                             .fetchall()[0])
                self.ClientNowInRoom = True
                print(f'[LOG] Appointment start for {N}')

        except IndexError:
            print("[LOG] Nobody in queue")

        except Exception as err:
            print(err)

    def cell_was_clicked(self):
        try:
            row = self.table.currentItem().row()
            self.SelectedRow = row
            print(f"[LOG] Client clicked on {row} row in table")
        except Exception as err:
            print(err)

    def closeEvent(self, event):
        try:
            self.parent.show()
            print(f"[LOG] Window closed")
        except Exception as err:
            print(err)


class CheckIn(QDialog):
    def __init__(self, IDdoctor, IDpacient, parent=None):
        super(CheckIn, self).__init__(parent)
        self.parent = parent
        self.DoctorID = IDdoctor
        self.PacientID = IDpacient
        global cursor
        global sql

        try:
            uic.loadUi('SelectTime.ui', self)

            self.setWindowTitle('Выберите время')
            self.setModal(True)

            self.calendar.setMinimumDate(QDate(date.today().year, date.today().month, date.today().day))

            self.Worktime = cursor.execute(
                f"""SELECT start, end FROM working_hours WHERE doctor_id = {self.DoctorID}""").fetchall()
            self.DoctorName = cursor.execute(
                f"""select surname, name, patronymic from specialists where id = {self.DoctorID}""").fetchall()
            self.speciality = cursor.execute(
                f"""select speciality from specialists where id = {self.DoctorID}""").fetchall()

            self.Name.setText(
                f"Вы хотите записаться на приём к {' '.join(self.DoctorName[0])} ({self.speciality[0][0]})")
            self.WorkTime.setText(f'Врач принимет по будням с {self.Worktime[0][0]} до {self.Worktime[0][1]}')

            self.btn.clicked.connect(self.Actinon)

            print('[LOG] Exemplar "CheckIn" class created successfully')
        except Exception as err:
            print(err)

    def Actinon(self):
        try:
            global cursor
            global sql
            cursor.execute(f"""insert into schedule(client_id, doctor_id, date, time) values
             ({self.PacientID}, {self.DoctorID},
            '{'.'.join([str(self.calendar.selectedDate().day()), str(self.calendar.selectedDate().month()), str(self.calendar.selectedDate().year())])}
            ', '{':'.join([str(self.Time.time().hour()), str(self.Time.time().minute())])}')""")
            sql.commit()
            self.Succsessful.setText('Вы успешно записались к врачу. вы можете закрыть это окно')
        except Exception as err:
            print(err)

    def closeEvent(self, event):
        self.parent.show()


class Client(QDialog):
    def __init__(self, client_id, parent=None):  # + parent
        super(Client, self).__init__(parent)  #
        self.parent = parent  #
        global cursor
        global sql
        uic.loadUi('user.ui', self)
        self.logo.setPixmap(QPixmap('LOGO.png'))
        self.setWindowTitle('Яндекс.Поликлиника')
        self.setModal(True)
        Best_doctors_img = []
        Best_doctors_names = []
        with open('best_doctors.txt', 'r') as f:
            for i in f.readlines():
                file, name = i.split(';')
                Best_doctors_img.append(QPixmap(file))
                Best_doctors_names.append(str(name))
            self.photo_1.setPixmap(Best_doctors_img[0])
            self.photo_2.setPixmap(Best_doctors_img[1])
            self.photo_3.setPixmap(Best_doctors_img[2])
            self.photo_4.setPixmap(Best_doctors_img[3])
            self.photo_5.setPixmap(Best_doctors_img[4])
            self.photo_6.setPixmap(Best_doctors_img[5])
            self.photo_7.setPixmap(Best_doctors_img[6])
            self.photo_8.setPixmap(Best_doctors_img[7])
            self.name_1.setText(Best_doctors_names[0])
            self.name_2.setText(Best_doctors_names[1])
            self.name_3.setText(Best_doctors_names[2])
            self.name_4.setText(Best_doctors_names[3])
            self.name_5.setText(Best_doctors_names[4])
            self.name_6.setText(Best_doctors_names[5])
            self.name_7.setText(Best_doctors_names[6])
            self.name_8.setText(Best_doctors_names[7])
            self.Doctors.setFocusPolicy(QtCore.Qt.NoFocus)
            self.Doctors.setColumnCount(2)
            self.Doctors.setHorizontalHeaderLabels(["ФИО врача", "Специальность"])
            self.DoctorsList = []
            for i in cursor.execute(f"""Select surname, name, patronymic, speciality from specialists""").fetchall():
                self.DoctorsList.append([str(i[0] + ' ' + i[1] + ' ' + i[2]), i[3]])
            self.Doctors.setRowCount(len(self.DoctorsList))
            Row = 0
            for i in self.DoctorsList:
                self.Doctors.setItem(Row, 0, QTableWidgetItem(i[0]))
                self.Doctors.setItem(Row, 1, QTableWidgetItem(i[1]))
                Row += 1
            self.Doctors.resizeColumnsToContents()

            self.appointment.setColumnCount(4)
            self.appointment.setHorizontalHeaderLabels(["ФИО врача", "Специальность", "Дата записи", "Время записи"])
            self.id = client_id
            result = cursor.execute(f"""
            select s.surname, s.name, s.patronymic, s.speciality, sc.time, sc.date from specialists s, schedule sc
            where s.id in (select sc.doctor_id from schedule sc where sc.client_id = {self.id})
            """).fetchall()
            queue = []
            notregistered = False
            try:
                for element in result:
                    queue.append(list(el for el in element))
            except IndexError:
                notregistered = True
            if notregistered:
                self.appointment.setRowCount(1)
                self.appointment.setItem(0, 1, QTableWidgetItem('Вы ни к кому не записаны'))
            else:
                self.appointment.setRowCount(len(queue))
                Row = 0
                for i in queue:
                    self.appointment.setItem(Row, 0, QTableWidgetItem(str(i[0] + ' ' + i[1] + ' ' + i[2])))
                    self.appointment.setItem(Row, 1, QTableWidgetItem(i[3]))
                    self.appointment.setItem(Row, 2, QTableWidgetItem(i[5]))
                    self.appointment.setItem(Row, 3, QTableWidgetItem(i[4]))
                    Row += 1

            self.appointment.setFocusPolicy(QtCore.Qt.NoFocus)
            self.appointment.resizeColumnsToContents()
            self.Doctors.cellClicked.connect(self.cell_was_clicked)

            self.imsick.clicked.connect(self.sick)
            print('[LOG] exemplar "Client" class created successfully')

    def sick(self):
        CheckIn(self.DoctorID, self.id, self.parent).show()
        print('[LOG] "Записаться" button was clicked')

    def cell_was_clicked(self):
        global cursor
        global sql
        row = self.Doctors.currentItem().row()
        Doctor = self.DoctorsList[int(row)]
        self.DoctorID = cursor.execute(
            f"""select id from specialists where speciality = '{Doctor[1]}' and surname = '{Doctor[0].split()[0]}'""").fetchall()[
            0][0]
        print(f"[LOG] Client clicked on {row} row in table")

    def open_additional_registration(self, user):
        global cursor
        global sql
        i = cursor.execute(f'''
        select id from accounts where account = '{user}'
        ''').fetchone()
        CheckIn(self.N, self.parent).show()
        print('[LOG] Create window additional registration successful')

    def closeEvent(self, event):  # +++
        self.parent.show()


class Authorization(QDialog):
    def __init__(self, parent=None):
        super(Authorization, self).__init__(parent)
        self.parent = parent

        self.Image = QImage("бежевый.jpg")
        self.Image = self.Image.scaled(QSize(900, 900))
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.Image))
        self.setPalette(self.palette)

        self.setWindowTitle('Вход')
        self.setModal(True)
        self.login = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.authorization = QPushButton()
        self.authorization.setText('Войти')
        self.form = QtWidgets.QFormLayout()
        self.error = QLabel(self)
        self.added = False

        self.form.addRow("&Логин:", self.login)
        self.form.addRow("&Пароль:", self.password)
        self.form.addRow(self.authorization)

        self.authorization.clicked.connect(self.open_account)

        self.setLayout(self.form)
        print('[LOG] Exemplar "Authorization" class created successfully')

    def open_account(self):
        global sql
        global cursor
        error_message = ['аккаунт' if not self.login.text() else None, 'пароль' if not self.password.text() else None]
        if any(error_message):
            if not self.added:
                self.added = True
                self.form.addRow(self.error)
            self.error.setText(f'Введите {" и ".join(list(filter(None, error_message)))}.')
        else:
            try:
                account, correct_password, role, gmail, index = cursor.execute(f'''
                select * from accounts where account = '{self.login.text()}'
                ''').fetchone()
                if self.password.text() == correct_password:
                    if role == 'client':
                        self.open_client(index)
                    else:
                        self.open_doctor(index)
                else:
                    if not self.added:
                        self.added = True
                        self.form.addRow(self.error)
                    self.error.setText('Неверно указан пароль.')
                    print('[LOG] wrong password')

            except TypeError:
                if not self.added:
                    self.added = True
                    self.form.addRow(self.error)
                self.error.setText('Такого аккаунта не существует.')
                print('[LOG] wrong account')

    def open_client(self, client_id):
        Client(client_id, self.parent).show()
        print('[LOG] Create client diagalog')

    def open_doctor(self, doctor_id):
        try:
            Doctor(doctor_id, self.parent).show()
            print('[LOG] Create doctor diagalog')
        except Exception as err:
            print(err)

    def closeEvent(self, event):
        self.parent.show()
        print('[LOG] Window closed')


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.parent = parent

        self.Image = QImage("бежевый.jpg")
        self.Image = self.Image.scaled(QSize(900, 900))
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.Image))
        self.setPalette(self.palette)

        self.btn_auth = QtWidgets.QPushButton("&Войти")
        self.btn_auth.clicked.connect(self.open_dialog_authorization)
        self.btn_reg = QtWidgets.QPushButton("&Зарегистрироваться")
        self.btn_reg.clicked.connect(self.open_dialog_registration)
        self.v_box = QtWidgets.QVBoxLayout()
        self.v_box.addWidget(self.btn_auth)
        self.v_box.addWidget(self.btn_reg)
        self.setLayout(self.v_box)
        print('[LOG] Exemplar "CentralWidget" class created successfully')

    def open_dialog_authorization(self):
        print('[LOG] Open dialog authorization successful')
        Authorization(self.parent).show()

    def open_dialog_registration(self):
        print('[LOG] Open dialog registration successful')
        Registration(self.parent).show()

    def stop_dialog(self):
        self.dialog.destroy()
        print('[LOG] Window closed')


class AddRegDialog(QDialog):
    def __init__(self, index, parent=None):
        super(AddRegDialog, self).__init__(parent)
        self.parent = parent
        self.index = index

        self.Image = QImage("бежевый.jpg")
        self.Image = self.Image.scaled(QSize(900, 900))
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.Image))
        self.setPalette(self.palette)

        self.setWindowTitle('Регистрация')
        self.setModal(True)

        self.name = QtWidgets.QLineEdit()
        self.surname = QtWidgets.QLineEdit()
        self.patronymic = QtWidgets.QLineEdit()

        self.gender = QComboBox(self)
        self.gender.addItems(['Мужской', 'Женский', 'Андроген', 'Бигендер', 'FTM', 'Гендерфлюид', 'Небинарный',
                              'Транс-мужчина', 'Транс-женщина', 'Квир', 'Бесполый', 'Под вопросом', 'Другой',
                              'Предпочитаю не указывать'])

        self.day = QComboBox(self)
        self.day.addItems([str(i) for i in range(1, 32)])
        self.month = QComboBox(self)
        self.month.addItems([str(i) for i in range(1, 13)])
        self.year = QComboBox(self)
        self.year.addItems([str(i) for i in range(2000, date.today().year + 1)])

        self.date = QtWidgets.QHBoxLayout()
        self.date.addWidget(self.day)
        self.date.addWidget(self.month)
        self.date.addWidget(self.year)

        self.address = QtWidgets.QLineEdit()

        self.form = QtWidgets.QFormLayout()
        self.form.setSpacing(20)

        self.form.addRow("&Имя:", self.name)
        self.form.addRow("&Фамилия:", self.surname)
        self.form.addRow("&Отчество (при наличии):", self.patronymic)
        self.form.addRow("&Гендер", self.gender)
        self.form.addRow("Дата рождения:", self.date)
        self.form.addRow("Адрес проживания", self.address)
        self.error = QLabel(self)
        self.registration = QPushButton()
        self.registration.setText('Закончить регистрацию')
        self.registration.clicked.connect(self.final_registration)
        self.form.addRow(self.registration)
        self.added = False

        self.setLayout(self.form)

        print('[LOG] exemplar "AddRegDialog" class created successfully')

    def final_registration(self):
        global cursor
        global sql

        if self.name.text() and self.surname.text() and self.address.text():
            cursor.execute(f'''
            insert into clients ('id', 'surname', 'name', 'patronymic', 'state', 'address', 'birth', 'gender')
            values ('{self.index}', '{self.surname.text().capitalize()}', '{self.name.text().capitalize()}', 
            '{self.patronymic.text().capitalize() if self.patronymic.text() else '-'}', 
            '{'здорова' if self.gender.currentText() == 'Женский' else 'здоров'}', '{self.address.text()}', 
            '{date(int(self.year.currentText()), int(self.month.currentText()), int(self.day.currentText()))}',
            '{'жен' if self.gender.currentText() == 'Женский' else 'муж'}')
            ''')  # inserting basic information about the new client
            sql.commit()

        else:
            if not self.added:
                self.added = True
                self.form.addRow(self.error)  # for the first time we hope that the new user isn't blind but inattentive
                self.error.setText('Неполные данные')
            else:
                message = ['имя' if not self.name.text() else None, 'фамилию' if not self.surname.text() else None,
                           'адрес' if not self.address.text() else None,  # checking how blind he is
                           'при наличии - отчество' if not self.patronymic.text() else None]

                self.error.setText(f'Введите, пожалуйста: {", ".join(list(filter(None, message)))}.')
        print('[LOG] regestation complited successful')

    def closeEvent(self, event):
        self.parent.show()
        print('[LOG] Window closed')


class Registration(QDialog):
    def __init__(self, parent=None):
        super(Registration, self).__init__(parent)
        self.parent = parent

        self.Image = QImage("бежевый.jpg")
        self.Image = self.Image.scaled(QSize(900, 900))
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.Image))
        self.setPalette(self.palette)
        self.error_message = QLabel('Error')
        self.FirstPressOnRegButton = True
        self.FirstTimeError = True

        self.setWindowTitle('Регистрация')
        self.setModal(True)
        self.line_user = QtWidgets.QLineEdit()
        self.line_pass = QtWidgets.QLineEdit()
        self.line_pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.line_post = QtWidgets.QLineEdit()
        self.registration = QPushButton()
        self.registration.setText('Зарегистрироваться')
        self.registration.clicked.connect(self.authorization)
        self.form = QtWidgets.QFormLayout()

        self.form.addRow("&Логин:", self.line_user)
        self.form.addRow("&Пароль:", self.line_pass)
        self.form.addRow("&Почта", self.line_post)
        self.form.addRow(self.registration)
        self.message = ''
        self.code = 1
        self.true_code = 0

        self.setLayout(self.form)

        print('[LOG] exemplar "Registration" class created successfully')

    def send_authorization_message(self, code):
        address_from = "yandex.hospital@gmail.com"
        password = "8bukvIodnacifra"
        address_to = self.line_post.text()
        msg = MIMEMultipart()
        msg['From'] = address_from
        msg['To'] = address_to
        msg['Subject'] = 'Регистрация'

        body = f"Ваш код подтверждения {code}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('imap.gmail.com', 587)
        server.set_debuglevel(True)
        server.starttls()
        server.login(address_from, password)
        server.send_message(msg)
        server.quit()

        print('[LOG] Email send')

    def authorization(self):
        global cursor
        global sql
        if self.FirstPressOnRegButton:
            try:  # checking if the email and login are unique values and correct
                if good_password(self.line_pass.text()) and good_email(self.line_post.text()) \
                        and good_login(self.line_user.text()):
                    if not self.FirstTimeError:
                        self.form.removeRow(3)
                    self.true_code = str(random.randint(100000, 999999))
                    self.send_authorization_message(self.true_code)

                    self.message = QLabel('Введите код из письма:')
                    self.code = QtWidgets.QLineEdit()

                    self.form.insertRow(3, self.code)
                    self.form.insertRow(3, self.message)
                    self.FirstPressOnRegButton = False
                else:

                    if not good_password(self.line_pass.text()):
                        self.error_message.setText('Пароль слишком прост!')
                    elif not good_email(self.line_post.text()):
                        self.error_message.setText('Неверный e-mail адрес!')
                    elif not good_login(self.line_user.text()):
                        self.error_message.setText('Такой логин уже существует!')
                    if self.FirstTimeError:
                        self.FirstTimeError = False
                        self.form.insertRow(3, self.error_message)
                    else:
                        self.form.removeRow(3)
                        self.form.insertRow(3, self.error_message)
            except Exception as err:
                print(f'[ERROR REPORT] {err}')  # to change later
        else:
            if self.code.text() != self.true_code:
                self.message.setText('Неверный код')
            else:
                cursor.execute(f'''
                insert into accounts ('account', 'password', 'role', 'email')
                values ('{self.line_user.text()}', '{self.line_pass.text()}', 'client', '{self.line_post.text()}')
                ''')  # inserting info about the new user's account into users.db
                sql.commit()
                self.open_additional_registration(self.line_user.text())
        print('[LOG] authorization comlite (1rst part)')

    def open_additional_registration(self, user):
        global cursor
        global sql
        i = cursor.execute(f'''
        select id from accounts where account = '{user}'
        ''').fetchone()
        AddRegDialog(i[0], self.parent).show()

    def closeEvent(self, event):
        self.parent.show()
        self.setWindowTitle('Регистрация аккаунта')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hospital")
        self.setGeometry(300, 300, 300, 200)
        self.Image = QImage("бежевый.jpg")
        self.Image = self.Image.scaled(QSize(300, 300))
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.Image))
        self.setPalette(self.palette)

        self.central = CentralWidget(self)
        self.setCentralWidget(self.central)
        self.statusBar()
        self.central.open_dialog_authorization()
        print('[LOG] Main winow create succsessful')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
