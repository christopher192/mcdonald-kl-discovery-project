import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, CardBody, CardHeader } from 'reactstrap';
import { GoogleApiWrapper, Map, Marker, Circle, InfoWindow } from "google-maps-react";
import BreadCrumb from '../../Components/Common/BreadCrumb';

const LoadingContainer = () => <div>Loading...</div>

const Home2 = (props) => {
    document.title = "Google Maps";

    const [currentLocation, setCurrentLocation] = useState({ lat: 3.1390, lng: 101.6869 });
    const [outlets, setOutlets] = useState(null);
    const [selectedOutlet, setSelectedOutlet] = useState(null);

    const mapStyles = {
        width: '100%',
        height: '100%',
    };

    const handleMarkerMouseover = (props, marker, e) => {
        setSelectedOutlet(props.outlet);
    }

    const handleMarkerMouseout = (props, marker, e) => {
        setSelectedOutlet(null);
    }

    useEffect(() => {
        fetch('http://127.0.0.1:5000/get_outlets_geodesic')
            .then(response => response.json())
            .then(data => {
                setOutlets(data["data"]);
            })
            .catch(error => console.error('Error:', error));
    }, []);

    return (
        <React.Fragment>
            <div className="page-content">
                <Container fluid>
                    <BreadCrumb title="Google Maps" pageTitle="Home" />
                    <Row>
                        <Col>
                            <Card>
                                <CardHeader>
                                    <h4 className="card-title mb-0">MCDonald (Kuala Lumpur)</h4>
                                </CardHeader>
                                <CardBody>
                                    <div id="gmaps-markers" className="gmaps" style={{ position: "relative", height: 500 }}>
                                        {outlets !== null && (
                                            <Map
                                                google={props.google}
                                                zoom={11}
                                                style={mapStyles}
                                                initialCenter={currentLocation}
                                            >
                                                {outlets.map((outlet, index) => (
                                                    <Marker
                                                        key={index}
                                                        position={{ lat: outlet.latitude, lng: outlet.longitude }}
                                                        onClick={() => {}}
                                                        onMouseover={handleMarkerMouseover}
                                                        onMouseout={handleMarkerMouseout}
                                                        outlet={outlet}
                                                    />
                                                ))}
                                                {outlets.map((outlet, index) => (
                                                    <Circle
                                                        key={index}
                                                        radius={5000} // 5km
                                                        center={{ lat: outlet.latitude, lng: outlet.longitude }}
                                                        strokeColor='#FF0000'
                                                        strokeOpacity={0.8}
                                                        strokeWeight={2}
                                                        fillColor={outlet.intersects_5km === 1 ? '#00FF00' : 'transparent'}
                                                    />
                                                ))}
                                                {selectedOutlet && (
                                                    <InfoWindow
                                                        position={{ lat: selectedOutlet.latitude, lng: selectedOutlet.longitude }}
                                                        visible={true}
                                                    >
                                                        <div>
                                                            <h6>{selectedOutlet.name}</h6>
                                                        </div>
                                                    </InfoWindow>
                                                )}
                                            </Map>
                                        )}
                                    </div>
                                </CardBody>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            </div>
        </React.Fragment>
    );
}

export default (
    GoogleApiWrapper({
        apiKey: "AIzaSyAbvyBxmMbFhrzP9Z8moyYr6dCr-pzjhBE",
        LoadingContainer: LoadingContainer,
        v: "3",
    })(Home2)
);
