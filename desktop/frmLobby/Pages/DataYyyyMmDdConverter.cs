using System;
using System.Globalization;
using System.Windows.Data;

namespace WindowLobby.Pages
{
    
    public class DataYyyyMmDdConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var texto = value as string;

            if (ViagensPage.TryParseData(texto, out var data))
                return data.ToString("yyyy/MM/dd");

            return texto ?? "";
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }
}
