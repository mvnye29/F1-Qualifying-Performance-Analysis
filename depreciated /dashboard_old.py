from panel.template import DarkTheme
import panel as pn
import pandas as pd
import hvplot.pandas



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
        width=300,
        styles={
            'background': '#f8f9fa',
            'border': '1px solid #dee2e6',
            'border-radius': '8px',
            'padding': '8px',
            'font-family': 'Inter, sans-serif'
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
                pn.pane.Markdown("Please select a driver", styles={'font-family': 'Inter, sans-serif'})
            )
        
        def create_year_panel(year_data: pd.Series) -> pn.Column:
            """
            Create panel visualization for a specific year.
            
            Args:
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
                color='#dc3545' ,
            )).opts(
                padding=0.1,
                show_grid=True,
                fontsize={'labels': 14, 'xticks': 12, 'yticks': 12, 'title': 20},
                xrotation=45,
                margin=(50,50,100,50),
                tools=['box_zoom', 'reset'],
                xlabel='Qualifying Event',
                ylabel='Qualifying Position',
                width=1500,
                height=400,
                bgcolor='#f8f9fa',
                axiswise=True,
                ylim=(20,0),
            )

            scatter_plot = scatter_plot.opts(
                xticks=[(i, race) for i, race in enumerate(plot_df['round'].tolist())], 
                xlabel='Qualifying Event',
            )

            valid_pos_df = plot_df.dropna(subset=['Position'])
            best_position = valid_pos_df['Position'].min() if not valid_pos_df.empty else "N/A"
            best_races = valid_pos_df[valid_pos_df['Position'] == best_position]['round'].tolist() if not valid_pos_df.empty else []
            
            header = pn.Column(
                pn.Row(
                    pn.pane.Markdown(
                        f"🏆 **Best Qualifying Position:** P{best_position:.0f}" if best_position != "N/A" else "🏆 **Best Position:** N/A",
                        styles={'font-size': '18px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                    ),
                    pn.pane.Markdown(
                        f"📅 **P{best_position:.0f} Achieved at:** {', '.join(best_races)}" if best_position != "N/A" else "📅 **Best Position Achieved at:** N/A",
                        styles={'font-size': '18px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                    ),
                    styles={'gap': '20px'}
                )
            )

            pole_gap_str = f"+{year_data['avgGapToPole']:.3f}" if year_data['avgGapToPole'] > 0 else f"{year_data['avgGapToPole']:.3f}"

            metrics = pn.Row(
                pn.pane.Markdown(f"🏎 **Team:** {year_data['team']}", styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
                pn.pane.Markdown(f"📊 **Avg Qualifying Position:** P{year_data['avgQualifyingPosition']:.0f}", styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
                pn.pane.Markdown(f"⏱ **Avg Gap to Pole:** {pole_gap_str}s", styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
                pn.pane.Markdown(f"🔄 **Avg Gap to Teammate:** {year_data['avgTeammateGap']:+.3f}s", styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}),
                styles={'gap': '20px'}
            )
            
            race_selector = pn.widgets.Select(
                name='Select Race',
                options=all_races,
                value=all_races[0] if all_races else None,
                width=300,
                styles={
                    'background': '#f8f9fa',
                    'border': '1px solid #dee2e6',
                    'border-radius': '8px',
                    'padding': '8px',
                    'font-family': 'Inter, sans-serif'
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
                }
            )

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
                        f"🏁 **{driver}'s Qualifying Position:** {position}",
                        styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                    ),
                    pn.pane.Markdown(
                        f"⏱ **Gap to Pole:** {pole_gap}",
                        styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
                    ),
                    pn.pane.Markdown(
                        f"🔄 **Gap to Teammate:** {teammate_gap}",
                        styles={'font-size': '16px', 'background': '#fff', 'padding': '10px', 'border-radius': '8px', 'border': '1px solid #dee2e6'}
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
        
        driver_data = df[df['driver'] == driver].sort_values('year')
        timeline_panels = [create_year_panel(year_data) for _, year_data in driver_data.iterrows()]
        
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