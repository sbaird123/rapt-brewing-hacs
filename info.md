# RAPT Brewing Session Manager

A comprehensive Home Assistant integration for managing brewing sessions with RAPT Pill hydrometers.

## Features

🍺 **Complete Brewing Session Management**
- Start, stop, pause, and resume brewing sessions
- Track multiple sessions with historical data
- Fermentation stage management (primary → secondary → conditioning → packaging)

📊 **Advanced Calculations**
- Automatic ABV percentage calculation
- Real-time attenuation tracking
- Fermentation rate monitoring (SG/hour)
- Temperature trend analysis

🔔 **Smart Alerts**
- Stuck fermentation detection
- Temperature warnings (high/low)
- Fermentation completion notifications
- Low battery alerts

📈 **Rich Monitoring**
- 16 comprehensive sensors
- Real-time gravity and temperature tracking
- Historical data analysis
- Dashboard-ready configuration

## Prerequisites

- Home Assistant 2023.9.0 or later
- RAPT BLE integration installed and configured
- RAPT Pill hydrometer device

## Quick Start

1. Install via HACS (see installation instructions)
2. Add integration in Home Assistant
3. Configure with your RAPT device ID
4. Import the included dashboard configuration
5. Start your first brewing session!

## Sensors Included

- **Session Management**: Name, state, stage, duration
- **Gravity Readings**: Original, current, target gravity
- **Calculated Values**: ABV%, attenuation%, fermentation rate
- **Environmental**: Temperature readings and targets
- **Device Status**: Battery, signal strength, connectivity
- **Statistics**: Total sessions, active alerts, timing

## Dashboard Ready

Includes complete Lovelace dashboard configuration with:
- Session control panel
- Real-time monitoring cards
- Historical charts and graphs
- Progress tracking
- Alert management

Perfect for homebrewers who want professional-grade brewing session management!