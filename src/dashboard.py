from panel.template import DarkTheme
import panel as pn
import pandas as pd
import hvplot.pandas
import holoviews as hv

pn.extension(sizing_mode="stretch_width")
pn.config.sizing_mode = "stretch_width"

def create_driver_timeline(timeline_data: pd.DataFrame) -> pn.Column:
    """
    Create an interactive driver timeline dashboard.
    
    Args:
        timeline_data: DataFrame containing driver career data
        
    Returns:
        Panel Column containing the complete dashboard
    """

    df = pd.DataFrame(timeline_data)
    all_drivers = sorted(df['driver'].unique().tolist())
    
    driver_selector = pn.widgets.Select(
        name='Select Driver',
        options=all_drivers,
        value=all_drivers[0],
        width=500,
        styles={
            'background': '#f8f9fa',
            'border': '1px solid #dee2e6',
            'border-radius': '8px',
            'padding': '8px',
            'font-family': 'Inter, sans-serif',
            'font-size': '18px'
        }
    )
    
    def create_timeline(driver: str) -> pn.Column:
        """
        Create timeline visualization for a specific driver.

        Args:
            driver: Name of the driver to visualize
            
        Returns:
            Panel Column containing the driver's timeline
        """

        if not driver:
            return pn.Column(
                pn.pane.Markdown("Select Driver", styles={'font-family': 'Inter, sans-serif'})
            )
        
        driver_data = df[df['driver'] == driver].sort_values('year')
        
        # Group by year to detect multiple team stints
        timeline_panels = []
        for year, year_group in driver_data.groupby('year'):
            if len(year_group) > 1:
                # Multiple teams in one year - create combined panel
                year_panel = create_multi_team_year_panel(driver, year, year_group)
            else:
                # Single team for the year
                year_panel = create_year_panel(driver, year_group.iloc[0])
            
            timeline_panels.append(year_panel)
        
        return pn.Column(
            pn.pane.Markdown(
                f"<h1>{driver}'s Performance Timeline</h1>",
                styles={
                    'font-size': '36px',
                    'font-weight': '700',
                    'font-family': 'Inter, sans-serif',
                    'margin-bottom': '30px',
                    'color': '#212529',
                    'text-align': 'center',
                    'cursor': 'default'
                }
            ),
            *timeline_panels,
            styles={'gap': '30px'}
        )
    
    def create_multi_team_year_panel(driver: str, year: int, year_data: pd.DataFrame) -> pn.Column:
        """
        Create a combined panel for a year with multiple team stints.
        
        Args:
            driver: Name of the driver
            year: Season year
            year_data: DataFrame containing all stints for this year
            
        Returns:
            Panel Column containing the multi-team year visualization
        """
        
        # Year header with team change indicator
        year_marker = pn.pane.Markdown(
            f"<h1>{year} <span style='font-size: 20px; color: #dc3545;'>⚠️ Mid-Season Team Change</span></h1>",
            styles={
                'margin-bottom': '15px',
                'padding': '15px',
                'font-size': '28px',
                'font-weight': '600',
                'font-family': 'Inter, sans-serif',
                'color': '#212529',
                'cursor': 'default'
            }
        )
        
        # Collect all events and data from all stints
        all_events_data = []
        stint_info_panels = []
        
        for idx, (_, stint_data) in enumerate(year_data.iterrows()):
            stint_info = stint_data.get('teamStintInfo', {})
            
            # Create stint header
            stint_header = pn.pane.Markdown(
                f"**{stint_data['team']}** ({stint_info.get('eventRange', 'N/A')})",
                styles={
                    'font-size': '24px',
                    'font-weight': '600',
                    'color': '#495057',
                    'padding': '8px 12px',
                    'background': '#e9ecef',
                    'border-radius': '6px',
                    'margin-bottom': '8px',
                    'display': 'inline-block'
                }
            )
            
            # Create metrics for this stint
            pole_gap_str = f"+{stint_data['avgGapToPole']:.3f}" if stint_data['avgGapToPole'] > 0 else f"{stint_data['avgGapToPole']:.3f}"
            
            stint_metrics = pn.Row(
                pn.pane.Markdown(f"**Avg Pos:** P{stint_data['avgQualifyingPosition']:.0f}", 
                                styles={'font-size': '20px', 'background': '#fff', 'padding': '8px', 'border-radius': '6px', 'border': '1px solid #dee2e6'}),
                pn.pane.Markdown(f"**Avg Gap to Pole:** {pole_gap_str}s", 
                                styles={'font-size': '20px', 'background': '#fff', 'padding': '8px', 'border-radius': '6px', 'border': '1px solid #dee2e6'}),
                pn.pane.Markdown(f"**Avg Gap to Teammate:** {stint_data['avgTeammateGap']:+.3f}s", 
                                styles={'font-size': '20px', 'background': '#fff', 'padding': '8px', 'border-radius': '6px', 'border': '1px solid #dee2e6'}),
                styles={'gap': '15px', 'margin-bottom': '10px'}
            )
            
            stint_info_panels.append(
                pn.Column(
                    stint_header,
                    stint_metrics,
                    styles={
                        'border-left': '4px solid #dc3545',
                        'padding-left': '15px',
                        'margin-bottom': '15px'
                    }
                )
            )
            
            # Collect event data from this stint
            for event in stint_data['events']:
                if 'position' in event and 'round' in event:
                    all_events_data.append({
                        'driver': stint_data['driver'],
                        'team': stint_data['team'],
                        'round': event['round'],
                        'Position': event['position'],
                        'gapToPole': event.get('gapToPole', None),
                        'teammateGap': event.get('teammateGap', None),
                        'hasTeammateData': event.get('hasTeammateData', False)
                    })
        
        # Create combined visualization
        if all_events_data:
            combined_viz = create_combined_year_visualization(driver, year, all_events_data, year_data)
        else:
            combined_viz = pn.pane.Markdown("No data available for visualization")
        
        return pn.Column(
            year_marker,
            pn.Row(
                *stint_info_panels,
                styles={
                    'background': '#f8f9fa',
                    'padding': '15px',
                    'border-radius': '8px',
                    'margin-bottom': '15px',
                    'gap': '20px'
                }
            ),
            combined_viz,
            pn.layout.Divider(margin=(30, 0)),
            styles={
                'background': '#ffffff',
                'padding': '20px',
                'border-radius': '12px',
                'border': '1px solid #dee2e6',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
                'margin-top': '10px',
            },
            sizing_mode='stretch_width'
        )
    
    def create_combined_year_visualization(driver: str, year: int, all_events_data: list, year_data: pd.DataFrame) -> pn.Column:
        """
        Create a combined visualization showing all events across team changes.
        
        Args:
            driver: Driver name
            year: Season year
            all_events_data: List of event dictionaries from all stints
            year_data: DataFrame containing stint information
            
        Returns:
            Panel Column with combined visualization
        """
        
        plot_df = pd.DataFrame(all_events_data)
        
        # Create ordered categorical for rounds
        all_rounds = plot_df['round'].unique().tolist()
        plot_df['round'] = pd.Categorical(plot_df['round'], categories=all_rounds, ordered=True)
        plot_df = plot_df.sort_values('round')
        
        # Create complete dataframe with all rounds
        complete_df = pd.DataFrame({'round': all_rounds})
        complete_df['round'] = pd.Categorical(complete_df['round'], categories=all_rounds, ordered=True)
        complete_df = complete_df.merge(plot_df, on='round', how='left')
        
        plot_df['RoundNumber'] = plot_df['round'].cat.codes
        complete_df['RoundNumber'] = complete_df['round'].cat.codes
        
        # Create base plot
        scatter_plot = (plot_df.hvplot.line(
            'RoundNumber', 'Position',
            color='#dc3545',
            alpha=0.3,
            line_width=2,
        ) * complete_df.hvplot.scatter(
            'RoundNumber', 'Position',
            size=30,
            color='#dc3545',
        )).opts(
            padding=0,
            show_grid=True,
            fontsize={'labels': 14, 'xticks': 12, 'yticks': 12, 'title': 20},
            xrotation=45,
            margin=(50, 50, 100, 50),
            tools=['box_zoom', 'reset'],
            xlabel='Qualifying Event',
            ylabel='Qualifying Position',
            width=1500,
            height=500,
            responsive=False,
            bgcolor='#f8f9fa',
            axiswise=True,
            xlim=(0, len(all_rounds) - 1),
            ylim=(20, 0),
        )
        
        scatter_plot = scatter_plot.opts(
            xticks=[(i, race) for i, race in enumerate(all_rounds)],
            xlabel='Qualifying Event',
        )
        
        # Add vertical lines for team changes
        if len(year_data) > 1:
            # Find transition points between teams
            stint_transitions = []
            for idx, (_, stint) in enumerate(year_data.iterrows()):
                if idx > 0:  # Skip first stint
                    stint_info = stint.get('teamStintInfo', {})
                    start_event = stint_info.get('start_event')
                    if start_event and start_event in all_rounds:
                        transition_idx = all_rounds.index(start_event)
                        stint_transitions.append(transition_idx)
            
            # Add vertical lines at transitions
            for transition in stint_transitions:
                vline = hv.VLine(transition).opts(
                    color='#dc3545',
                    line_dash='dashed',
                    line_width=2,
                    alpha=0.6
                )
                scatter_plot = scatter_plot * vline
        
        # Calculate overall year statistics
        valid_pos_df = plot_df.dropna(subset=['Position'])
        best_position = valid_pos_df['Position'].min() if not valid_pos_df.empty else "N/A"
        best_races = valid_pos_df[valid_pos_df['Position'] == best_position]['round'].tolist() if not valid_pos_df.empty else []
        
        avg_position = valid_pos_df['Position'].mean() if not valid_pos_df.empty else "N/A"
        
        header = pn.Column(
            pn.Row(
                pn.pane.Markdown(
                    f"🏆 **Best Qualifying Position:** P{best_position:.0f}" if best_position != "N/A" else "🏆 **Best Position:** N/A",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**P{best_position:.0f} Achieved at:** {', '.join(best_races)}" if best_position != "N/A" else "**Best Position Achieved at:** N/A",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**Overall Avg Position:** P{avg_position:.0f}" if avg_position != "N/A" else "**Overall Avg Position:** N/A",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                styles={'gap': '20px'}
            )
        )
        
        # Race selector
        race_selector = pn.widgets.Select(
            name='Select Race',
            options=all_rounds,
            value=all_rounds[0] if all_rounds else None,
            width=400,
            styles={
                'background': '#f8f9fa',
                'border': '1px solid #dee2e6',
                'border-radius': '8px',
                'padding': '8px',
                'font-family': 'Inter, sans-serif',
                'font-size': '18px'
            }
        )
        
        race_details = pn.Row(styles={'gap': '20px'})
        event_title = pn.pane.Markdown("", styles={
            'font-size': '22px',
            'font-family': 'Inter, sans-serif',
            'color': '#212529',
            'margin': '0',
            'align-self': 'center',
            'flex-grow': '1'
        })
        
        def update_race_details(event: None) -> None:
            """Update race details panel based on selected race."""
            selected_round = race_selector.value
            filtered_race_data = complete_df[complete_df['round'] == selected_round]
            event_title.object = f"**Showing Specific Event Details For:** {selected_round}"
            
            if not filtered_race_data.empty and not filtered_race_data['Position'].isna().all():
                race_data = filtered_race_data.iloc[0]
                position = f"P{race_data['Position']:.0f}"
                team = race_data.get('team', 'N/A')
                pole_gap = f"+{race_data['gapToPole']:.3f}s" if pd.notna(race_data['gapToPole']) else "No Data"
                teammate_gap = f"{race_data['teammateGap']:+.3f}s" if race_data['hasTeammateData'] else "No Teammate Data"
            else:
                position = "Did Not Qualify"
                team = "N/A"
                pole_gap = "N/A"
                teammate_gap = "N/A"
            
            race_details.clear()
            race_details.extend([
                pn.pane.Markdown(
                    f"🏎 **Team:** {team}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**{driver}'s Qualifying Position:** {position}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**Gap to Pole:** {pole_gap}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**Gap to Teammate:** {teammate_gap}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                )
            ])
        
        update_race_details(None)
        race_selector.param.watch(update_race_details, 'value')
        
        return pn.Column(
            header,
            pn.pane.HoloViews(scatter_plot, margin=(20, 0), sizing_mode='stretch_width'),
            pn.Row(
                event_title,
                race_selector,
                styles={
                    'font-size': '22px',
                    'font-family': 'Inter, sans-serif',
                    'color': '#212529',
                    'margin': '0',
                    'justify-content': 'space-between'
                }
            ),
            race_details,
            sizing_mode='stretch_width'
        )
    
    def create_year_panel(driver: str, year_data: pd.Series) -> pn.Column:
        """
        Create panel visualization for a specific year.
        
        Args:
            driver: Name of the driver
            year_data: Series containing driver data for one year
            
        Returns:
            Panel Column containing the year's visualization
        """
        
        plot_data = []
        events = year_data['events']
        
        for event in events:
            if 'position' in event and 'round' in event:
                plot_data.append({
                    'driver': year_data['driver'],
                    'round': event['round'],
                    'Position': event['position'],
                    'gapToPole': event.get('gapToPole', None),
                    'teammateGap': event.get('teammateGap', None),
                    'hasTeammateData': event.get('hasTeammateData', False)
                })
        
        plot_df = pd.DataFrame(plot_data)
        plot_df['round'] = pd.Categorical(plot_df['round'], categories=plot_df['round'].tolist(), ordered=True)
        
        all_races = [event['round'] for event in events if 'round' in event]
        
        complete_df = pd.DataFrame({'round': all_races})
        complete_df['round'] = pd.Categorical(complete_df['round'], categories=plot_df['round'].tolist(), ordered=True)
        
        complete_df = complete_df.merge(plot_df, on='round', how='left')

        plot_df = plot_df.sort_values('round')
        complete_df = complete_df.sort_values('round')

        plot_df['RoundNumber'] = plot_df['round'].cat.codes
        complete_df['RoundNumber'] = complete_df['round'].cat.codes
        
        complete_df['round'] = pd.Categorical(
            complete_df['round'],
            categories=all_races,
            ordered=True
        )
        
        complete_df = complete_df.sort_values('round')
        
        year_marker = pn.pane.Markdown(
            f"<h1>{year_data['year']}</h1>",
            styles={
                'margin-bottom': '15px',
                'padding': '15px',
                'font-size': '28px',
                'font-weight': '600',
                'font-family': 'Inter, sans-serif',
                'color': '#212529',
                'cursor': 'default'
            }
        )
        
        scatter_plot = (plot_df.hvplot.line(
            'RoundNumber', 'Position',
            color='#dc3545',
            alpha=0.3,
            line_width=2,
        ) * complete_df.hvplot.scatter(
            'RoundNumber', 'Position',
            size=30,
            color='#dc3545',
        )).opts(
            padding=0.1,
            show_grid=True,
            fontsize={'labels': 14, 'xticks': 12, 'yticks': 12, 'title': 20},
            xrotation=45,
            margin=(50, 50, 100, 50),
            tools=['box_zoom', 'reset'],
            xlabel='Qualifying Event',
            ylabel='Qualifying Position',
            width=1500,
            height=500,
            responsive=False,
            bgcolor='#f8f9fa',
            axiswise=True,
            xlim=(0, len(all_races) - 1),
            ylim=(20, 0),
        )

        scatter_plot = scatter_plot.opts(
            xticks=[(i, race) for i, race in enumerate(plot_df['round'].tolist())],
            xlabel='Qualifying Event',
        )

        scatter_plot.opts(xlim=(0, len(all_races)-1))

        valid_pos_df = plot_df.dropna(subset=['Position'])
        best_position = valid_pos_df['Position'].min() if not valid_pos_df.empty else "N/A"
        best_races = valid_pos_df[valid_pos_df['Position'] == best_position]['round'].tolist() if not valid_pos_df.empty else []
        
        header = pn.Column(
            pn.Row(
                pn.pane.Markdown(
                    f"🏆 **Best Qualifying Position:** P{best_position:.0f}" if best_position != "N/A" else "🏆 **Best Position:** N/A",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**P{best_position:.0f} Achieved at:** {', '.join(best_races)}" if best_position != "N/A" else "**Best Position Achieved at:** N/A",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                styles={'gap': '20px'}
            )
        )

        pole_gap_str = f"+{year_data['avgGapToPole']:.3f}" if year_data['avgGapToPole'] > 0 else f"{year_data['avgGapToPole']:.3f}"

        metrics = pn.Row(
            pn.pane.Markdown(f"🏎 **Team:** {year_data['team']}", styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
            pn.pane.Markdown(f"**Avg Qualifying Position:** P{year_data['avgQualifyingPosition']:.0f}", styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
            pn.pane.Markdown(f"**Avg Gap to Pole:** {pole_gap_str}s", styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
            pn.pane.Markdown(f"**Avg Gap to Teammate:** {year_data['avgTeammateGap']:+.3f}s", styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
            styles={'gap': '20px'}
        )
        
        race_selector = pn.widgets.Select(
            name='Select Race',
            options=all_races,
            value=all_races[0] if all_races else None,
            width=400,
            styles={
                'background': '#f8f9fa',
                'border': '1px solid #dee2e6',
                'border-radius': '8px',
                'padding': '8px',
                'font-family': 'Inter, sans-serif',
                'font-size': '18px'
            }
        )

        race_details = pn.Row(styles={'gap': '20px'})
        event_title = pn.pane.Markdown("", styles={
            'font-size': '22px',
            'font-family': 'Inter, sans-serif',
            'color': '#212529',
            'margin': '0',
            'align-self': 'center',
            'flex-grow': '1'
        })

        def update_race_details(event: None) -> None:
            """
            Update race details panel based on selected race.
            
            Args:
                event: Panel event trigger (not used)
            """

            selected_round = race_selector.value
            filtered_race_data = complete_df[complete_df['round'] == selected_round]
            event_title.object = f"**Showing Specific Event Details For:** {selected_round}"
            
            if not filtered_race_data.empty and not filtered_race_data['Position'].isna().all():
                race_data = filtered_race_data.iloc[0]
                position = f"P{race_data['Position']:.0f}"
                pole_gap = f"+{race_data['gapToPole']:.3f}s" if pd.notna(race_data['gapToPole']) else "No Data"
                teammate_gap = f"{race_data['teammateGap']:+.3f}s" if race_data['hasTeammateData'] else "No Teammate Data"
            else:
                position = "Did Not Qualify"
                pole_gap = "N/A"
                teammate_gap = "N/A"

            race_details.clear()
            race_details.extend([
                pn.pane.Markdown(
                    f"**{driver}'s Qualifying Position:** {position}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**Gap to Pole:** {pole_gap}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                ),
                pn.pane.Markdown(
                    f"**Gap to Teammate:** {teammate_gap}",
                    styles={'font-size': '23px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                )
            ])
        
        update_race_details(None)
        race_selector.param.watch(update_race_details, 'value')
        
        return pn.Column(
            pn.Column(
                year_marker,
                styles={'margin-bottom': '10px'},
                sizing_mode='stretch_width'
            ),
            pn.Column(
                header,
                metrics,
                pn.pane.HoloViews(scatter_plot, margin=(20, 0), sizing_mode='stretch_width'),
                pn.Row(
                    event_title,
                    race_selector,
                    styles={
                        'font-size': '22px',
                        'font-family': 'Inter, sans-serif',
                        'color': '#212529',
                        'margin': '0',
                        'justify-content': 'space-between'
                    }
                ),
                race_details,
                styles={
                    'background': '#ffffff',
                    'padding': '20px',
                    'border-radius': '12px',
                    'border': '1px solid #dee2e6',
                    'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'margin-top': '10px',
                },
                sizing_mode='stretch_width'
            ),
            pn.layout.Divider(margin=(30, 0)),
            sizing_mode='stretch_width'
        )
    
    dynamic_panel = pn.bind(create_timeline, driver_selector)
    
    return pn.Column(
        pn.Row(
            driver_selector,
            styles={'justify-content': 'center', 'margin': '20px 0'}
        ),
        pn.layout.Divider(),
        dynamic_panel,
        styles={
            'background': '#f8f9fa',
            'padding': '20px'
        }
    )

career_timeline_data = pd.read_json('../data/career_timeline.json')

dashboard = create_driver_timeline(career_timeline_data)
dashboard.show()