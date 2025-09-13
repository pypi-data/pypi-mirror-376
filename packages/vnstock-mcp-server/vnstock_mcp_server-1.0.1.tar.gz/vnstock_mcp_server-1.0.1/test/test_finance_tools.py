import pytest
import pandas as pd
import json
from unittest.mock import patch, Mock
from src.vnstock_mcp.server import (
    get_income_statements,
    get_balance_sheets,
    get_cash_flows,
    get_finance_ratios,
    get_raw_report
)


class TestFinanceTools:
    """Test suite for finance-related tools"""

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_income_statements_json(self, mock_vci_finance_class, sample_financial_data):
        """Test get_income_statements with JSON output"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.income_statement.return_value = sample_financial_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_income_statements('VCB', 'year', 'json')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='year')
        mock_instance.income_statement.assert_called_once()
        
        # Verify JSON output
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert isinstance(parsed_result, list)
        assert len(parsed_result) == 2
        assert parsed_result[0]['period'] == '2023'
        assert parsed_result[0]['revenue'] == 50000000000

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_income_statements_dataframe(self, mock_vci_finance_class, sample_financial_data):
        """Test get_income_statements with DataFrame output"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.income_statement.return_value = sample_financial_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_income_statements('VCB', 'quarter', 'dataframe')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='quarter')
        mock_instance.income_statement.assert_called_once()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]['period'] == '2023'

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_balance_sheets_json(self, mock_vci_finance_class, sample_financial_data):
        """Test get_balance_sheets with JSON output"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.balance_sheet.return_value = sample_financial_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_balance_sheets('VCB', 'year', 'json')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='year')
        mock_instance.balance_sheet.assert_called_once()
        
        parsed_result = json.loads(result)
        assert len(parsed_result) == 2
        assert parsed_result[0]['total_assets'] == 2000000000000

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_balance_sheets_dataframe(self, mock_vci_finance_class, sample_financial_data):
        """Test get_balance_sheets with DataFrame output"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.balance_sheet.return_value = sample_financial_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_balance_sheets('VCB', 'quarter', 'dataframe')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='quarter')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]['total_assets'] == 2000000000000

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_cash_flows_returns_dataframe_directly(self, mock_vci_finance_class, sample_financial_data):
        """Test get_cash_flows - note: this function returns DataFrame directly without format conversion"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.cash_flow.return_value = sample_financial_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_cash_flows('VCB', 'year', 'json')  # Even with 'json', it returns DataFrame
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='year')
        mock_instance.cash_flow.assert_called_once()
        
        # The function has a bug - it doesn't respect output_format parameter
        assert isinstance(result, pd.DataFrame)  # Should be JSON string but returns DataFrame
        assert len(result) == 2

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_finance_ratios_json(self, mock_vci_finance_class):
        """Test get_finance_ratios with JSON output"""
        # Setup mock
        sample_ratios = pd.DataFrame([
            {
                'period': '2023',
                'pe_ratio': 12.5,
                'pb_ratio': 2.1,
                'roe': 0.18,
                'roa': 0.015,
                'debt_to_equity': 0.5
            },
            {
                'period': '2022',
                'pe_ratio': 11.8,
                'pb_ratio': 1.9,
                'roe': 0.16,
                'roa': 0.013,
                'debt_to_equity': 0.6
            }
        ])
        
        mock_instance = Mock()
        mock_instance.ratio.return_value = sample_ratios
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_finance_ratios('VCB', 'year', 'json')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='year')
        mock_instance.ratio.assert_called_once()
        
        parsed_result = json.loads(result)
        assert len(parsed_result) == 2
        assert parsed_result[0]['pe_ratio'] == 12.5

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_finance_ratios_dataframe(self, mock_vci_finance_class):
        """Test get_finance_ratios with DataFrame output"""
        # Setup mock
        sample_ratios = pd.DataFrame([{
            'period': '2023',
            'pe_ratio': 12.5,
            'current_ratio': 1.2
        }])
        
        mock_instance = Mock()
        mock_instance.ratio.return_value = sample_ratios
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_finance_ratios('VCB', 'quarter', 'dataframe')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='quarter')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['pe_ratio'] == 12.5

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_raw_report_json(self, mock_vci_finance_class):
        """Test get_raw_report with JSON output"""
        # Setup mock
        sample_raw_data = pd.DataFrame([
            {
                'period': '2023',
                'metric_code': 'REV001',
                'metric_name': 'Total Revenue',
                'value': 50000000000,
                'unit': 'VND'
            },
            {
                'period': '2023',
                'metric_code': 'PROFIT001',
                'metric_name': 'Net Profit',
                'value': 12000000000,
                'unit': 'VND'
            }
        ])
        
        mock_instance = Mock()
        mock_instance._get_report.return_value = sample_raw_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_raw_report('VCB', 'year', 'json')
        
        # Assertions
        mock_vci_finance_class.assert_called_once_with(symbol='VCB', period='year')
        mock_instance._get_report.assert_called_once_with(mode='raw')
        
        parsed_result = json.loads(result)
        assert len(parsed_result) == 2
        assert parsed_result[0]['metric_code'] == 'REV001'

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_get_raw_report_dataframe(self, mock_vci_finance_class):
        """Test get_raw_report with DataFrame output"""
        # Setup mock
        sample_raw_data = pd.DataFrame([{
            'period': '2023',
            'metric_code': 'REV001',
            'value': 50000000000
        }])
        
        mock_instance = Mock()
        mock_instance._get_report.return_value = sample_raw_data
        mock_vci_finance_class.return_value = mock_instance
        
        # Test
        result = get_raw_report('VCB', 'quarter', 'dataframe')
        
        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['metric_code'] == 'REV001'

    @pytest.mark.unit
    def test_finance_tools_default_parameters(self):
        """Test finance tools with default parameters"""
        with patch('src.vnstock_mcp.server.VCIFinance') as mock_vci_finance_class:
            mock_instance = Mock()
            mock_instance.income_statement.return_value = pd.DataFrame([{'period': '2023'}])
            mock_vci_finance_class.return_value = mock_instance
            
            # Test default period (should be 'year') and output_format (should be 'json')
            result = get_income_statements('VCB')
            mock_vci_finance_class.assert_called_with(symbol='VCB', period='year')
            assert isinstance(result, str)  # JSON string

    @pytest.mark.unit
    def test_finance_tools_with_different_periods(self):
        """Test finance tools with different period parameters"""
        with patch('src.vnstock_mcp.server.VCIFinance') as mock_vci_finance_class:
            mock_instance = Mock()
            mock_instance.balance_sheet.return_value = pd.DataFrame([{'period': '2023Q1'}])
            mock_vci_finance_class.return_value = mock_instance
            
            # Test quarterly period
            result = get_balance_sheets('VCB', 'quarter', 'json')
            mock_vci_finance_class.assert_called_with(symbol='VCB', period='quarter')
            
            # Test yearly period
            result = get_balance_sheets('VCB', 'year', 'json')
            mock_vci_finance_class.assert_called_with(symbol='VCB', period='year')

    @pytest.mark.unit
    def test_finance_tools_error_handling(self):
        """Test error handling in finance tools"""
        with patch('src.vnstock_mcp.server.VCIFinance') as mock_vci_finance_class:
            mock_instance = Mock()
            mock_instance.income_statement.side_effect = Exception("Invalid symbol")
            mock_vci_finance_class.return_value = mock_instance
            
            with pytest.raises(Exception):
                get_income_statements('INVALID', 'year', 'json')

    @pytest.mark.unit
    def test_finance_tools_empty_results(self):
        """Test finance tools with empty results"""
        with patch('src.vnstock_mcp.server.VCIFinance') as mock_vci_finance_class:
            mock_instance = Mock()
            mock_instance.ratio.return_value = pd.DataFrame()
            mock_vci_finance_class.return_value = mock_instance
            
            result = get_finance_ratios('VCB', 'year', 'json')
            assert result == '[]'
            
            result = get_finance_ratios('VCB', 'year', 'dataframe')
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    @pytest.mark.unit
    @patch('src.vnstock_mcp.server.VCIFinance')
    def test_all_finance_tools_with_same_symbol(self, mock_vci_finance_class):
        """Test all finance tools with the same symbol to ensure consistency"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.income_statement.return_value = pd.DataFrame([{'revenue': 1000}])
        mock_instance.balance_sheet.return_value = pd.DataFrame([{'assets': 5000}])
        mock_instance.cash_flow.return_value = pd.DataFrame([{'cash_flow': 500}])
        mock_instance.ratio.return_value = pd.DataFrame([{'pe_ratio': 12.5}])
        mock_instance._get_report.return_value = pd.DataFrame([{'raw_data': 'test'}])
        mock_vci_finance_class.return_value = mock_instance
        
        symbol = 'VCB'
        period = 'year'
        
        # Test all tools
        income_result = get_income_statements(symbol, period, 'dataframe')
        balance_result = get_balance_sheets(symbol, period, 'dataframe')
        cash_result = get_cash_flows(symbol, period, 'dataframe')
        ratio_result = get_finance_ratios(symbol, period, 'dataframe')
        raw_result = get_raw_report(symbol, period, 'dataframe')
        
        # All should be DataFrames
        assert isinstance(income_result, pd.DataFrame)
        assert isinstance(balance_result, pd.DataFrame)
        assert isinstance(cash_result, pd.DataFrame)  # This one has the bug
        assert isinstance(ratio_result, pd.DataFrame)
        assert isinstance(raw_result, pd.DataFrame)
        
        # All should have called with same parameters
        assert mock_vci_finance_class.call_count == 5
        for call in mock_vci_finance_class.call_args_list:
            assert call[1]['symbol'] == symbol
            assert call[1]['period'] == period

    @pytest.mark.unit
    def test_cash_flows_bug_documentation(self):
        """Test and document the bug in get_cash_flows function"""
        with patch('src.vnstock_mcp.server.VCIFinance') as mock_vci_finance_class:
            mock_instance = Mock()
            sample_data = pd.DataFrame([{'cash_flow': 1000}])
            mock_instance.cash_flow.return_value = sample_data
            mock_vci_finance_class.return_value = mock_instance
            
            # This should return JSON string but returns DataFrame due to bug
            result = get_cash_flows('VCB', 'year', 'json')
            
            # Current behavior (bug): returns DataFrame instead of JSON
            assert isinstance(result, pd.DataFrame)
            # Expected behavior would be: assert isinstance(result, str)
            
            # The function ignores output_format parameter
            result_df = get_cash_flows('VCB', 'year', 'dataframe')
            assert isinstance(result_df, pd.DataFrame)
            
            # Both calls return the same type (DataFrame) regardless of output_format
