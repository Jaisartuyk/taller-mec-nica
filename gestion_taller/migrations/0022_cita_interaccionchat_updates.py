# Generated manually on 2025-08-23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_taller', '0021_auto_20250823_1838'),
    ]

    operations = [
        # Create Cita model
        migrations.CreateModel(
            name='Cita',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_cita', models.DateTimeField()),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada'), ('completada', 'Completada')], default='pendiente', max_length=20)),
                ('notas', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas', to='gestion_taller.cliente')),
                ('conductor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas', to='gestion_taller.conductor')),
                ('servicios', models.ManyToManyField(related_name='citas', to='gestion_taller.serviciocatalogo')),
                ('vehiculo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas', to='gestion_taller.vehiculo')),
            ],
            options={
                'verbose_name': 'Cita',
                'verbose_name_plural': 'Citas',
                'ordering': ['-fecha_cita'],
            },
        ),
        
        # Update InteraccionChat model - add missing fields
        migrations.AddField(
            model_name='interaccionchat',
            name='telefono',
            field=models.CharField(default='', help_text='Número de teléfono del contacto', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='interaccionchat',
            name='respuesta',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='interaccionchat',
            name='resuelta',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='interaccionchat',
            name='satisfaccion',
            field=models.SmallIntegerField(blank=True, help_text='Calificación de satisfacción del 1 al 5', null=True),
        ),
        
        # Update InteraccionChat related_name to avoid conflicts
        migrations.AlterField(
            model_name='interaccionchat',
            name='conductor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='interacciones_chat', to='gestion_taller.conductor'),
        ),
        
        # Update InteraccionChat meta options
        migrations.AlterModelOptions(
            name='interaccionchat',
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'Interacción de chat', 'verbose_name_plural': 'Interacciones de chat'},
        ),
    ]
