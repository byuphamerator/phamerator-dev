import logger

class errorHandler:
  def __init__(self):
    self._logger = logger.logger(True)
  def show_sql_errors(self, c):
    c.execute("SHOW WARNINGS")
    errors = c.fetchall()
    for error in errors:
      self._logger.log(error)
