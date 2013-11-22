# coding=utf-8
#
#   yadt-config-rpm-maker
#   Copyright (C) 2011-2013 Immobilien Scout GmbH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from logging import ERROR
from mock import Mock, call, patch
from unittest import TestCase

from config_rpm_maker.config import DEFAULT_LOG_LEVEL, DEFAULT_SYS_LOG_LEVEL
from config_rpm_maker.logutils import create_console_handler, create_sys_log_handler, log_configuration


@patch('config_rpm_maker.logutils.StreamHandler')
@patch('config_rpm_maker.logutils.Formatter')
class CreateConsoleHandlerTests(TestCase):

    def test_should_initialze_formatter_and_use_it(self, mock_formatter_class, mock_stream_handler_class):

        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        mock_handler = Mock()
        mock_stream_handler_class.return_value = mock_handler

        create_console_handler()

        mock_formatter_class.assert_called_with('[%(levelname)5s] %(message)s')
        mock_handler.setFormatter.assert_called_with(mock_formatter)

    def test_should_set_default_log_level_if_no_log_level_given(self, mock_formatter_class, mock_stream_handler_class):

        mock_handler = Mock()
        mock_stream_handler_class.return_value = mock_handler

        create_console_handler()

        mock_handler.setLevel.assert_called_with(DEFAULT_LOG_LEVEL)

    def test_should_set_given_log_level(self, mock_formatter_class, mock_stream_handler_class):

        mock_handler = Mock()
        mock_stream_handler_class.return_value = mock_handler

        create_console_handler(log_level=ERROR)

        mock_handler.setLevel.assert_called_with(ERROR)

    def test_should_return_created_console_handler(self, mock_formatter_class, mock_stream_handler_class):

        mock_handler = Mock()
        mock_stream_handler_class.return_value = mock_handler

        actual_handler = create_console_handler()

        self.assertEqual(mock_handler, actual_handler)


@patch('config_rpm_maker.logutils.SysLogHandler')
@patch('config_rpm_maker.logutils.Formatter')
class CreateSysLogHandlerTests(TestCase):

    def test_should_initialze_formatter_using_the_revision_number_in_the_format(self, mock_formatter_class, mock_sys_log_handler_class):

        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        mock_handler = Mock()
        mock_sys_log_handler_class.return_value = mock_handler

        create_sys_log_handler(123)

        mock_formatter_class.assert_called_with('config_rpm_maker[123]: [%(levelname)5s] %(message)s')
        mock_handler.setFormatter.assert_called_with(mock_formatter)

    def test_should_set_default_log_level_if_no_log_level_given(self, mock_formatter_class, mock_sys_log_handler_class):

        mock_handler = Mock()
        mock_sys_log_handler_class.return_value = mock_handler

        create_sys_log_handler(123)

        mock_handler.setLevel.assert_called_with(DEFAULT_SYS_LOG_LEVEL)

    def test_should_return_created_console_handler(self, mock_formatter_class, mock_sys_log_handler_class):

        mock_handler = Mock()
        mock_sys_log_handler_class.return_value = mock_handler

        actual_handler = create_sys_log_handler(123)

        self.assertEqual(mock_handler, actual_handler)


class LogConfigurationTests(TestCase):

    def setUp(self):
        self.mock_log = Mock()

    def test_should_log_given_path(self):

        log_configuration(self.mock_log, {}, 'configuration_file.yaml')

        self.assertEqual(call('Loaded configuration file "%s"', 'configuration_file.yaml'), self.mock_log.call_args_list[0])

    def test_should_log_when_configuration_file_was_empty(self):

        log_configuration(self.mock_log, {}, 'configuration_file.yaml')

        self.assertEqual(call('Configuration file was empty!'), self.mock_log.call_args_list[1])

    def test_should_log_given_string_configuration_property(self):

        log_configuration(self.mock_log, {'property': '123'}, 'configuration_file.yaml')

        self.assertEqual(call('Configuraton property %s = "%s" (%s)', '"property"', '123', 'str'), self.mock_log.call_args_list[1])

    def test_should_log_given_boolean_configuration_property(self):

        log_configuration(self.mock_log, {'property': True}, 'configuration_file.yaml')

        self.assertEqual(call('Configuraton property %s = "%s" (%s)', '"property"', True, 'bool'), self.mock_log.call_args_list[1])

    def test_should_log_given_integer_configuration_property(self):

        log_configuration(self.mock_log, {'property': 123}, 'configuration_file.yaml')

        self.assertEqual(call('Configuraton property %s = "%s" (%s)', '"property"', 123, 'int'), self.mock_log.call_args_list[1])

    def test_should_log_given_configuration_properties_in_alphabetical_order(self):

        configuration = {'a_property': 123,
                         'b_property': False,
                         'c_property': 'hello world'}

        log_configuration(self.mock_log, configuration, 'configuration_file.yaml')

        self.assertEqual([call('Loaded configuration file "%s"', 'configuration_file.yaml'),
                          call('Configuraton property %s = "%s" (%s)', '"a_property"', 123, 'int'),
                          call('Configuraton property %s = "%s" (%s)', '"b_property"', False, 'bool'),
                          call('Configuraton property %s = "%s" (%s)', '"c_property"', 'hello world', 'str')],
                         self.mock_log.call_args_list)
