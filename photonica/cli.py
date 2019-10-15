# -*- coding: utf-8 -*-

"""Console script for photonica."""
import sys
import click
import photonica


@click.command()
@click.option('--datapath', '-d', required=True,
              help='Path for data directory.')
@click.option('--offset_correction', '-o', type=int, default=0,
              help='Offset correction to use. Default = 0')
@click.option('--cropsize', '-c', type=tuple, default=(100, 100),
              help='Crop size in (x, y) format. Default=(100, 100).')
@click.option('--pedestal', '-p', type=int, default=10000,
              help='Pedestal to use in ADU. Default = 10000')
def main(datapath, offset_correction, cropsize, pedestal):
    """Console script for photonica."""
    click.echo('Importing from {}'.format(datapath))

    data = photonica.SensorData(offset_correction=offset_correction,
                                cropsize=cropsize, pedestal=pedestal)

    data.addFiles(datapath)

    data.calcStats()

    # per-sub stats
    data.data_set.drop(columns=['data']).to_csv('./data_set.csv')

# summary data w/ noise characteristics
    data.data_summary.to_csv('./data_summary.csv')


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
