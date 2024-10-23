from django.shortcuts import render
from .models import Part
from django.utils import timezone
import pytz

def part_detail(request):
    # Fetch all parts from the database
    parts = Part.objects.all()

    # Get the current time in UTC
    utc_time = timezone.now()

    # Define the Chicago timezone using pytz
    chicago_tz = pytz.timezone('America/Chicago')

    # Convert UTC time to Chicago timezone
    chicago_time = utc_time.astimezone(chicago_tz)

    return render(request, 'part_detail.html', {
        'parts': parts,             # Pass all parts to the template
        'current_time': chicago_time  # Pass the converted time to the template
    })
