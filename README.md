# Medical Appointments Dashboard

This repository contains a **Google Colab/Jupyter Notebook** implementation of a dashboard for analyzing and redistributing unused (idle) medical appointments.  
The project is developed in **Python** using **Plotly Dash** and **Dash Bootstrap Components**.

## Features
- **KPI Cards**: Quick overview of total available appointments, unused appointments, and utilization rates.
- **Trend Analysis**: Monthly evolution of idle appointments and percentage of unused slots.
- **Department Ranking**: Top/bottom departments by number of unused appointments.
- **Detailed Table**: Interactive table with filtering, sorting, and export to Excel.
- **Fair Redistribution Algorithm**: Suggests how unused appointments can be transferred from groups with surplus (donors) to groups with shortage (receivers), visualized with Sankey diagrams.

## Repository Structure
├── dashboard_notebook.ipynb # Main notebook with code
├── data/ # Folder for input CSV files (not included in repo)
├── README.md # This file
└── requirements.txt # Python dependencies
